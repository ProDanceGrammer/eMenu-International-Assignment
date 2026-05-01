"""
Data Normalizer Module

Handles data cleaning, normalization, and structuring of extracted menu data.
Processes raw text blocks into structured dish dictionaries.
"""

import re
from typing import List, Dict, Any, Optional


class DataNormalizer:
    """Normalizer for cleaning and structuring menu data."""

    # Pattern to match section headers (all caps, no price)
    SECTION_PATTERN = re.compile(r'^[A-Z\s&]+$')

    # Pattern to match prices ($XX or $X)
    PRICE_PATTERN = re.compile(r'\$\d+')

    # Pattern to match price placeholder
    PRICE_PLACEHOLDER_PATTERN = re.compile(r'\$X\b')

    def __init__(self):
        """Initialize normalizer."""
        self.current_category = None

    def normalize_dishes(self, text_blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Normalize text blocks into structured dish data.

        Args:
            text_blocks: List of text blocks from parser

        Returns:
            List of normalized dish dictionaries
        """
        dishes = []
        current_dish = None

        for block in text_blocks:
            text = block['text'].strip()

            if not text:
                continue

            # Check if this is a section header
            if self._is_section_header(text):
                self.current_category = self._normalize_text(text)
                continue

            # Check if this line contains a dish name and price
            if self._contains_price(text):
                # Save previous dish if exists
                if current_dish:
                    dishes.append(current_dish)

                # Start new dish
                current_dish = self._parse_dish_line(text)
            elif current_dish:
                # This is a continuation (description)
                current_dish['description'] = self._append_description(
                    current_dish.get('description', ''),
                    text
                )

        # Add last dish
        if current_dish:
            dishes.append(current_dish)

        return dishes

    def _is_section_header(self, text: str) -> bool:
        """
        Check if text is a section header.

        Args:
            text: Text to check

        Returns:
            True if text is a section header
        """
        # Section headers are typically all caps, no numbers, no prices
        if not text.isupper():
            return False

        if self.PRICE_PATTERN.search(text):
            return False

        # Check if it matches section pattern
        return bool(self.SECTION_PATTERN.match(text))

    def _contains_price(self, text: str) -> bool:
        """
        Check if text contains a price.

        Args:
            text: Text to check

        Returns:
            True if text contains a price or price placeholder
        """
        return bool(self.PRICE_PATTERN.search(text) or
                   self.PRICE_PLACEHOLDER_PATTERN.search(text))

    def _parse_dish_line(self, text: str) -> Dict[str, Any]:
        """
        Parse a line containing dish name and price.

        Args:
            text: Line of text with dish name and price

        Returns:
            Dictionary with dish_name, price, category
        """
        # Extract price
        price_match = self.PRICE_PATTERN.search(text)
        price = price_match.group(0) if price_match else None

        # Check for price placeholder
        if not price and self.PRICE_PLACEHOLDER_PATTERN.search(text):
            price = None  # Use null for placeholders

        # Extract dish name
        if price_match:
            # Check if price is at the beginning or end
            price_start = price_match.start()
            price_end = price_match.end()

            # If price is at the beginning (e.g., "$14 CHEESE WEDGES")
            if price_start < 5:  # Price within first few characters
                dish_name = text[price_end:].strip()
            else:
                # Price at the end (e.g., "CHEESE WEDGES $14")
                dish_name = text[:price_start].strip()
        else:
            dish_name = text.strip()

        dish_name = self._normalize_text(dish_name)

        return {
            'category': self.current_category,
            'dish_name': dish_name,
            'price': price,
            'description': ''
        }

    def _append_description(self, current_desc: str, new_text: str) -> str:
        """
        Append text to description, handling multi-line descriptions.

        Args:
            current_desc: Current description text
            new_text: New text to append

        Returns:
            Combined description
        """
        new_text = self._normalize_text(new_text)

        if not current_desc:
            return new_text

        # Add space between lines
        return f"{current_desc} {new_text}"

    def _normalize_text(self, text: str) -> str:
        """
        Normalize text by cleaning whitespace and formatting.

        Args:
            text: Text to normalize

        Returns:
            Normalized text
        """
        # Remove extra whitespace
        text = ' '.join(text.split())

        # Remove special characters that might cause issues
        text = text.replace('\t', ' ')
        text = text.replace('\n', ' ')

        return text.strip()

    def add_dish_ids(self, dishes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Add sequential dish IDs to dishes.

        Args:
            dishes: List of dish dictionaries

        Returns:
            List of dishes with dish_id field added
        """
        for idx, dish in enumerate(dishes, 1):
            dish['dish_id'] = f"{idx:03d}"  # Format as 001, 002, 003...

        return dishes

    def clean_descriptions(self, dishes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Clean up descriptions, removing empty ones.

        Args:
            dishes: List of dish dictionaries

        Returns:
            List of dishes with cleaned descriptions
        """
        for dish in dishes:
            desc = dish.get('description', '').strip()
            dish['description'] = desc if desc else ''

        return dishes
