#!/usr/bin/env python3
"""
Script to fix encoding issues in CSV files, particularly smart quotes and apostrophes
that were incorrectly decoded.
"""

import csv
import sys
from pathlib import Path

try:
    import ftfy
    HAS_FTFY = True
except ImportError:
    HAS_FTFY = False
    print("Warning: ftfy not installed. Install with: pip install ftfy")
    print("  Will use basic fixes instead.")

def fix_encoding_text(text: str) -> str:
    """
    Fix common encoding issues in text.
    Replaces incorrectly decoded smart quotes and apostrophes with standard ones.
    """
    if not text:
        return text
    
    # Common encoding issues:
    # â€™ -> ' (right single quotation mark/apostrophe)
    # â€œ -> " (left double quotation mark)
    # â€ -> " (right double quotation mark)
    # â€" -> — (em dash)
    # â€" -> – (en dash)
    # â€¦ -> … (ellipsis)
    
    replacements = {
        'â€™': "'",
        'â€œ': '"',
        'â€': '"',
        'â€"': '—',
        'â€"': '–',
        'â€¦': '…',
        'â€˜': "'",  # left single quotation mark
        'â€"': '—',  # em dash (alternative encoding)
        'â€"': '–',  # en dash (alternative encoding)
    }
    
    fixed = text
    for wrong, correct in replacements.items():
        fixed = fixed.replace(wrong, correct)
    
    return fixed

def fix_encoding_text_advanced(text: str) -> str:
    """
    Advanced fix for encoding issues.
    Handles the case where UTF-8 bytes were interpreted as Windows-1252.
    """
    if not text:
        return text
    
    # Use ftfy if available (best solution)
    if HAS_FTFY:
        text = ftfy.fix_text(text)
        # Then apply our standard fixes for any remaining issues
        return fix_encoding_text(text)
    
    # Fallback: manual fix
    # The pattern "â€™" represents UTF-8 bytes E2 80 99 (right single quote) 
    # that were interpreted as Windows-1252 characters
    try:
        # If the text contains these patterns, it was likely mis-encoded
        if 'â€™' in text or 'â€œ' in text or 'â€' in text:
            # Encode as Windows-1252 to get original bytes
            text_bytes = text.encode('windows-1252', errors='ignore')
            # Decode as UTF-8 to get correct characters
            text = text_bytes.decode('utf-8', errors='replace')
    except (UnicodeEncodeError, UnicodeDecodeError):
        pass
    
    # Apply standard fixes
    return fix_encoding_text(text)

def fix_csv_file(input_file: str, output_file: str = None) -> None:
    """
    Fix encoding issues in a CSV file.
    Reads file as binary first to properly handle encoding conversion.
    """
    input_path = Path(input_file)
    if not input_path.exists():
        print(f"Error: File {input_file} not found.")
        return
    
    if output_file is None:
        output_file = input_file
    
    print(f"Fixing encoding in {input_file}...")
    
    # Read file as binary first
    with open(input_file, 'rb') as f:
        raw_bytes = f.read()
    
    # Use ftfy if available (handles this automatically)
    if HAS_FTFY:
        # Decode as UTF-8 (or whatever it claims to be) and let ftfy fix it
        try:
            content = raw_bytes.decode('utf-8')
        except UnicodeDecodeError:
            content = raw_bytes.decode('utf-8', errors='replace')
        content = ftfy.fix_text(content)
    else:
        # Manual fix: Try to decode as UTF-8 first
        try:
            content = raw_bytes.decode('utf-8')
            # Check if it has the mis-encoding pattern
            if 'â€™' in content or 'â€œ' in content:
                # Re-encode as Windows-1252 then decode as UTF-8
                print("  Detected mis-encoded UTF-8, fixing...")
                content = raw_bytes.decode('windows-1252').encode('latin1').decode('utf-8')
        except (UnicodeDecodeError, UnicodeEncodeError):
            # If UTF-8 fails, try Windows-1252
            try:
                content = raw_bytes.decode('windows-1252')
                # Then try to fix by re-encoding
                content = content.encode('latin1').decode('utf-8', errors='replace')
            except (UnicodeDecodeError, UnicodeEncodeError):
                # Last resort: read as UTF-8 with error replacement
                content = raw_bytes.decode('utf-8', errors='replace')
    
    # Parse CSV from the fixed content
    import io
    rows = []
    reader = csv.reader(io.StringIO(content))
    header = next(reader)
    rows.append(header)
    
    for row in reader:
        fixed_row = [fix_encoding_text_advanced(cell) for cell in row]
        rows.append(fixed_row)
    
    # Write back as proper UTF-8
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(rows)
    
    print(f"Fixed encoding and saved to {output_file}")
    print(f"Processed {len(rows) - 1} data rows (plus header)")

def main():
    if len(sys.argv) < 2:
        print("Usage: python fix_encoding.py <input_csv> [output_csv]")
        print("  If output_csv is not specified, input_csv will be overwritten.")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    fix_csv_file(input_file, output_file)

if __name__ == '__main__':
    main()

