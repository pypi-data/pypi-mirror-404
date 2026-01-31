# Utilities Module

The `rotalabs_audit.utils` module provides common utility functions for text processing, ID generation, hashing, pattern extraction, and similarity calculation.

## Text Processing

Functions for cleaning, normalizing, and manipulating text.

### clean_text

Clean and normalize text by removing extra whitespace.

::: rotalabs_audit.utils.helpers.clean_text
    options:
      show_source: false
      heading_level: 4

### truncate_text

Truncate text with ellipsis, attempting to break at word boundaries.

::: rotalabs_audit.utils.helpers.truncate_text
    options:
      show_source: false
      heading_level: 4

### split_sentences

Split text into sentences using sentence-ending punctuation.

::: rotalabs_audit.utils.helpers.split_sentences
    options:
      show_source: false
      heading_level: 4

---

## Pattern Matching

Functions for extracting structured content from text using regex patterns.

### find_all_matches

Find all matches of a regex pattern in text.

::: rotalabs_audit.utils.helpers.find_all_matches
    options:
      show_source: false
      heading_level: 4

### extract_numbered_list

Extract items from a numbered list (1., 2., etc.).

::: rotalabs_audit.utils.helpers.extract_numbered_list
    options:
      show_source: false
      heading_level: 4

### extract_bullet_list

Extract items from a bullet list (-, *, etc.).

::: rotalabs_audit.utils.helpers.extract_bullet_list
    options:
      show_source: false
      heading_level: 4

---

## ID and Hashing

Functions for generating unique identifiers and content hashes.

### generate_id

Generate a unique ID for audit entries.

::: rotalabs_audit.utils.helpers.generate_id
    options:
      show_source: false
      heading_level: 4

### hash_content

Generate SHA-256 hash of content for integrity verification.

::: rotalabs_audit.utils.helpers.hash_content
    options:
      show_source: false
      heading_level: 4

---

## Similarity

Functions for calculating text similarity.

### calculate_text_similarity

Calculate Jaccard similarity (word overlap) between two texts.

::: rotalabs_audit.utils.helpers.calculate_text_similarity
    options:
      show_source: false
      heading_level: 4
