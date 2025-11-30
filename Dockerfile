# Multi-stage build for React + FastAPI

# Stage 1: Build React app
FROM node:18-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Python backend
FROM python:3.11-slim
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements and install
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./backend/
COPY dictionary.json ./backend/

# Copy built React app
COPY --from=frontend-builder /app/frontend/build ./frontend/build

# Expose port
EXPOSE 8000

# Run FastAPI (stay in backend directory so imports work)
# Database will be initialized on first run if it doesn't exist
WORKDIR /app/backend
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

