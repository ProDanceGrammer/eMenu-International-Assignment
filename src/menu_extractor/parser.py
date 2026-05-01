"""
PDF Parser Module

Handles PDF extraction using pdfplumber, preserving layout and structure.
Extracts text blocks with positioning data for two-column menu layouts.
"""

import pdfplumber
from typing import List, Dict, Any


class PDFParser:
    """Parser for extracting structured text from PDF menu files."""

    def __init__(self, pdf_path: str):
        """
        Initialize parser with PDF file path.

        Args:
            pdf_path: Path to the PDF file to parse
        """
        self.pdf_path = pdf_path

    def extract_text_blocks(self) -> List[Dict[str, Any]]:
        """
        Extract text blocks from PDF with positioning data.
        Handles two-column layout by separating columns first.

        Returns:
            List of text blocks with content and position information
        """
        blocks = []

        with pdfplumber.open(self.pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                # Extract words with positioning
                words = page.extract_words()

                # Get character-level data for font sizes
                chars = page.chars

                # Add font size directly to each word
                for word in words:
                    word['font_size'] = self._get_word_font_size(word, chars)

                # Separate into columns
                left_column, right_column = self._separate_columns(words)

                # Process left column
                left_lines = self._group_words_into_lines(left_column)
                for line in left_lines:
                    line['page'] = page_num
                    line['column'] = 'left'
                    blocks.append(line)

                # Process right column
                right_lines = self._group_words_into_lines(right_column)
                for line in right_lines:
                    line['page'] = page_num
                    line['column'] = 'right'
                    blocks.append(line)

        return blocks

    def _get_word_font_size(self, word: Dict, chars: List[Dict]) -> float:
        """
        Get font size for a word from character data.

        Args:
            word: Word dictionary
            chars: List of character dictionaries with font info

        Returns:
            Font size (most common size in the word)
        """
        # Find characters that belong to this word
        word_chars = [
            c for c in chars
            if (word['x0'] <= c['x0'] <= word['x1'] and
                abs(c['top'] - word['top']) < 2)
        ]

        if word_chars:
            # Use the most common font size in this word
            sizes = [c.get('size', 0) for c in word_chars if c.get('size', 0) > 0]
            if sizes:
                return max(set(sizes), key=sizes.count)

        return 0

    def _separate_columns(self, words: List[Dict]) -> tuple:
        """
        Separate words into left and right columns based on x-coordinate.

        Args:
            words: List of word dictionaries

        Returns:
            Tuple of (left_column_words, right_column_words)
        """
        if not words:
            return [], []

        # Find the midpoint of the page
        x_coords = [word['x0'] for word in words]
        min_x = min(x_coords)
        max_x = max(x_coords)
        midpoint = (min_x + max_x) / 2

        left_column = [word for word in words if word['x0'] < midpoint]
        right_column = [word for word in words if word['x0'] >= midpoint]

        return left_column, right_column

    def _group_words_into_lines(self, words: List[Dict]) -> List[Dict[str, Any]]:
        """
        Group words into lines based on vertical position.
        Detects subcolumns within lines based on x-coordinate gaps.

        Args:
            words: List of word dictionaries with position data

        Returns:
            List of line dictionaries with combined text and position
        """
        if not words:
            return []

        # Sort words by y-coordinate (top to bottom), then x-coordinate (left to right)
        sorted_words = sorted(words, key=lambda w: (round(w['top']), w['x0']))

        lines = []
        current_line = []
        current_y = None
        y_tolerance = 3  # Pixels tolerance for same line

        for word in sorted_words:
            word_y = round(word['top'])

            # Check if word belongs to current line
            if current_y is None or abs(word_y - current_y) <= y_tolerance:
                current_line.append(word)
                current_y = word_y
            else:
                # Start new line
                if current_line:
                    # Split line into subcolumns if needed
                    sublines = self._split_line_by_x_gaps(current_line)
                    lines.extend(sublines)
                current_line = [word]
                current_y = word_y

        # Add last line
        if current_line:
            sublines = self._split_line_by_x_gaps(current_line)
            lines.extend(sublines)

        return lines

    def _split_line_by_x_gaps(self, words: List[Dict]) -> List[Dict[str, Any]]:
        """
        Split a line into multiple items based on x-coordinate gaps.
        Large horizontal gaps indicate separate items in subcolumns.

        Args:
            words: List of words on the same line

        Returns:
            List of line dictionaries (one per subcolumn item)
        """
        if not words:
            return []

        # Sort words by x-coordinate
        sorted_words = sorted(words, key=lambda w: w['x0'])

        # Detect gaps between words
        X_GAP_THRESHOLD = 15  # Pixels - gap larger than this indicates new subcolumn

        sublines = []
        current_subline = [sorted_words[0]]

        for i in range(1, len(sorted_words)):
            prev_word = sorted_words[i - 1]
            curr_word = sorted_words[i]

            # Calculate gap between words
            gap = curr_word['x0'] - prev_word['x1']

            if gap > X_GAP_THRESHOLD:
                # Large gap - start new subcolumn
                if current_subline:
                    sublines.append(self._create_line_dict(current_subline))
                current_subline = [curr_word]
            else:
                # Same subcolumn
                current_subline.append(curr_word)

        # Add last subline
        if current_subline:
            sublines.append(self._create_line_dict(current_subline))

        return sublines

    def _create_line_dict(self, words: List[Dict]) -> Dict[str, Any]:
        """
        Create a line dictionary from a list of words.

        Args:
            words: List of word dictionaries

        Returns:
            Dictionary with combined text and position data
        """
        text = ' '.join(word['text'] for word in words)

        # Get font size from first word (stored in word['font_size'])
        size = words[0].get('font_size', 0) if words else 0

        return {
            'text': text,
            'x0': min(word['x0'] for word in words),
            'x1': max(word['x1'] for word in words),
            'top': min(word['top'] for word in words),
            'bottom': max(word['bottom'] for word in words),
            'fontname': words[0].get('fontname', ''),
            'size': size
        }

    def extract_raw_text(self) -> str:
        """
        Extract raw text from PDF (fallback method).

        Returns:
            Raw text content from all pages
        """
        text_parts = []

        with pdfplumber.open(self.pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)

        return '\n\n'.join(text_parts)
