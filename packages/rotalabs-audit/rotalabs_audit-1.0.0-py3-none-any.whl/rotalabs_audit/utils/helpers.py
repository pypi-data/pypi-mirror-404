"""
Utility functions for text processing and common operations.

This module provides helper functions for generating IDs, hashing content,
text manipulation, pattern extraction, and similarity calculation.
"""

import hashlib
import re
import uuid
from typing import List, Set


def generate_id(length: int = 8) -> str:
    """
    Generate a unique ID for audit entries.

    Generates a UUID-based identifier truncated to the specified length.

    Args:
        length: Number of characters for the ID (default: 8).

    Returns:
        A unique identifier string.

    Example:
        >>> id1 = generate_id()
        >>> len(id1)
        8
        >>> id2 = generate_id(12)
        >>> len(id2)
        12
    """
    return str(uuid.uuid4()).replace("-", "")[:length]


def hash_content(content: str) -> str:
    """
    Generate SHA-256 hash of content.

    Creates a deterministic hash of the input content for
    integrity verification and deduplication.

    Args:
        content: The content string to hash.

    Returns:
        The SHA-256 hash as a hexadecimal string.

    Example:
        >>> hash1 = hash_content("Hello, World!")
        >>> len(hash1)
        64
        >>> hash2 = hash_content("Hello, World!")
        >>> hash1 == hash2
        True
    """
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def split_sentences(text: str) -> List[str]:
    """
    Split text into sentences.

    Uses regex to split text at sentence boundaries.

    Args:
        text: The text to split into sentences.

    Returns:
        List of sentence strings.

    Example:
        >>> sentences = split_sentences("Hello! How are you? I'm fine.")
        >>> len(sentences)
        3
    """
    if not text:
        return []

    # Simple split on sentence-ending punctuation followed by whitespace
    # This avoids lookbehind issues with variable-width patterns
    pattern = r"[.!?]+\s+"

    sentences = re.split(pattern, text)

    # Clean up and filter empty sentences
    sentences = [s.strip() for s in sentences if s.strip()]

    return sentences


def clean_text(text: str) -> str:
    """
    Clean and normalize text.

    Removes extra whitespace, normalizes line endings, and
    strips leading/trailing whitespace.

    Args:
        text: The text to clean.

    Returns:
        Cleaned and normalized text.

    Example:
        >>> clean_text("  Hello   World  ")
        'Hello World'
        >>> clean_text("Line1\\n\\n\\nLine2")
        'Line1\\nLine2'
    """
    if not text:
        return ""

    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Replace multiple newlines with single newline
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Replace multiple spaces with single space (but preserve newlines)
    lines = text.split("\n")
    cleaned_lines = [re.sub(r" {2,}", " ", line).strip() for line in lines]

    # Rejoin and strip
    return "\n".join(cleaned_lines).strip()


def extract_numbered_list(text: str) -> List[str]:
    """
    Extract items from a numbered list (1., 2., etc.).

    Parses text to find numbered list items and returns their content.

    Args:
        text: The text containing a numbered list.

    Returns:
        List of item texts without the numbers.

    Example:
        >>> text = "1. First item\\n2. Second item\\n3. Third item"
        >>> items = extract_numbered_list(text)
        >>> items
        ['First item', 'Second item', 'Third item']
    """
    if not text:
        return []

    # Pattern for numbered items: "1.", "1)", "1:", etc.
    pattern = r"(?:^|\n)\s*(\d+)[\.\)\:]\s*([^\n]+)"

    matches = re.findall(pattern, text, re.MULTILINE)

    # Sort by number and extract content
    items = [(int(num), content.strip()) for num, content in matches if content.strip()]
    items.sort(key=lambda x: x[0])

    return [content for _, content in items]


def extract_bullet_list(text: str) -> List[str]:
    """
    Extract items from a bullet list (-, *, etc.).

    Parses text to find bullet list items and returns their content.

    Args:
        text: The text containing a bullet list.

    Returns:
        List of item texts without the bullets.

    Example:
        >>> text = "- First item\\n* Second item\\n- Third item"
        >>> items = extract_bullet_list(text)
        >>> items
        ['First item', 'Second item', 'Third item']
    """
    if not text:
        return []

    # Pattern for bullet items: "-", "*", "+", "•"
    pattern = r"(?:^|\n)\s*[-\*\+\u2022]\s*([^\n]+)"

    matches = re.findall(pattern, text, re.MULTILINE)

    return [match.strip() for match in matches if match.strip()]


def find_all_matches(
    pattern: str,
    text: str,
    flags: int = re.IGNORECASE,
) -> List[str]:
    """
    Find all matches of a regex pattern.

    Wrapper around re.findall with sensible defaults and
    error handling.

    Args:
        pattern: The regex pattern to search for.
        text: The text to search in.
        flags: Regex flags (default: re.IGNORECASE).

    Returns:
        List of all matches (or capture groups if pattern has groups).

    Example:
        >>> matches = find_all_matches(r"\\b(\\w+ing)\\b", "Running and jumping")
        >>> matches
        ['Running', 'jumping']
    """
    if not text or not pattern:
        return []

    try:
        return re.findall(pattern, text, flags)
    except re.error:
        # Invalid pattern
        return []


def calculate_text_similarity(text1: str, text2: str) -> float:
    """
    Calculate similarity between two texts.

    Uses Jaccard similarity (word overlap) to compute a similarity
    score between 0 and 1.

    Args:
        text1: First text.
        text2: Second text.

    Returns:
        Similarity score between 0.0 (no similarity) and 1.0 (identical).

    Example:
        >>> calculate_text_similarity("hello world", "hello there")
        0.333...
        >>> calculate_text_similarity("same text", "same text")
        1.0
    """
    if not text1 and not text2:
        return 1.0  # Both empty = identical

    if not text1 or not text2:
        return 0.0  # One empty, one not = no similarity

    # Tokenize: lowercase and split on non-word characters
    words1: Set[str] = set(re.findall(r"\b\w+\b", text1.lower()))
    words2: Set[str] = set(re.findall(r"\b\w+\b", text2.lower()))

    if not words1 and not words2:
        return 1.0  # Both have no words

    if not words1 or not words2:
        return 0.0

    # Jaccard similarity: intersection / union
    intersection = len(words1 & words2)
    union = len(words1 | words2)

    return intersection / union if union > 0 else 0.0


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text with ellipsis.

    Truncates text to the specified maximum length, adding a suffix
    if truncation occurs. Attempts to break at word boundaries.

    Args:
        text: The text to truncate.
        max_length: Maximum length including suffix (default: 100).
        suffix: String to append if truncated (default: "...").

    Returns:
        Truncated text with suffix if needed.

    Example:
        >>> truncate_text("Hello World", max_length=8)
        'Hello...'
        >>> truncate_text("Hi", max_length=10)
        'Hi'
    """
    if not text:
        return ""

    if len(text) <= max_length:
        return text

    # Calculate available space for text
    available = max_length - len(suffix)

    if available <= 0:
        return suffix[:max_length]

    # Try to break at word boundary
    truncated = text[:available]
    last_space = truncated.rfind(" ")

    if last_space > available // 2:
        # Break at word boundary if it's not too far back
        truncated = truncated[:last_space]

    return truncated.rstrip() + suffix


def normalize_whitespace(text: str) -> str:
    """
    Normalize all whitespace in text to single spaces.

    Replaces all whitespace sequences (spaces, tabs, newlines)
    with single spaces.

    Args:
        text: The text to normalize.

    Returns:
        Text with normalized whitespace.

    Example:
        >>> normalize_whitespace("Hello\\n\\tWorld  !")
        'Hello World !'
    """
    if not text:
        return ""

    return re.sub(r"\s+", " ", text).strip()


def extract_quoted_text(text: str) -> List[str]:
    """
    Extract all quoted text from a string.

    Finds text enclosed in single or double quotes.

    Args:
        text: The text to search.

    Returns:
        List of quoted strings (without the quotes).

    Example:
        >>> extract_quoted_text('He said "hello" and \\'goodbye\\'')
        ['hello', 'goodbye']
    """
    if not text:
        return []

    # Match both single and double quotes
    double_quoted = re.findall(r'"([^"]*)"', text)
    single_quoted = re.findall(r"'([^']*)'", text)

    return double_quoted + single_quoted


def count_words(text: str) -> int:
    """
    Count the number of words in text.

    Args:
        text: The text to count words in.

    Returns:
        Number of words.

    Example:
        >>> count_words("Hello World!")
        2
    """
    if not text:
        return 0

    return len(re.findall(r"\b\w+\b", text))


def is_question(text: str) -> bool:
    """
    Check if text appears to be a question.

    Args:
        text: The text to check.

    Returns:
        True if the text appears to be a question.

    Example:
        >>> is_question("How are you?")
        True
        >>> is_question("I am fine.")
        False
    """
    if not text:
        return False

    # Check for question mark
    if text.strip().endswith("?"):
        return True

    # Check for question words at the beginning
    question_words = [
        "what", "who", "where", "when", "why", "how",
        "is", "are", "was", "were", "do", "does", "did",
        "can", "could", "will", "would", "should",
    ]

    first_word = text.strip().split()[0].lower() if text.strip() else ""

    return first_word in question_words
