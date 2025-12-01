/**
 * Utility functions for URL handling
 */

/**
 * Convert a word name to a URL-safe string
 * Uses encodeURIComponent to handle special characters
 */
export const slugify = (word) => {
  return encodeURIComponent(word);
};

/**
 * Decode a slug back to word name
 */
export const unslugify = (slug) => {
  return decodeURIComponent(slug);
};

