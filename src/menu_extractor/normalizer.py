"""
Data Normalizer Module

Handles data cleaning, normalization, and structuring of extracted menu data.
Processes raw text blocks into structured dish dictionaries.
"""

import re
from typing import List, Dict, Any, Optional
from collections import Counter


class DataNormalizer:
    """Normalizer for cleaning and structuring menu data."""

    # Pattern to match section headers (all caps, no price)
    SECTION_PATTERN = re.compile(r'^[A-Z\s&]+$')

    # Pattern to match prices ($XX or $X)
    PRICE_PATTERN = re.compile(r'\$\d+')

    # Pattern to match price placeholder
    PRICE_PLACEHOLDER_PATTERN = re.compile(r'\$X\b')

    # Gap threshold for description boundary detection (pixels)
    GAP_THRESHOLD = 12

    # Category keywords for semantic header splitting
    CATEGORY_KEYWORDS = [
        'LEADING OFF', 'SLIDER TOWERS', 'JUMBO CHICKEN WINGS',
        'BREADED CHICKEN TENDERS', 'SIGNATURE SAUCES', 'FLIGHTS',
        'SALADS & SOUP', 'HANDHELDS', 'BURGERS', 'MAIN EVENT',
        'SIDES', 'OVERTIME', 'SIGNATURE COCKTAILS', 'ZERO PROOF',
        'DRAFT BEER', 'BOTTLES & CANS', 'WINES', 'ENERGY'
    ]

    # Pattern for sub-items (e.g., "6 WINGS", "12 WINGS")
    SUBITEM_PATTERN = re.compile(r'^\d+\s+[A-Z]+')

    # Subcategories that span multiple columns
    CROSS_COLUMN_SUBCATEGORIES = ['SIGNATURE SAUCES']

    def __init__(self):
        """Initialize normalizer."""
        self.current_category = None
        self.subcategories = {}  # Track multiple subcategories by x-coordinate: {x: subcategory_name}
        self.max_font_size = 0  # Track largest font size (categories)
        self.most_common_font_size = 0  # Track most common font size (items)

    def _analyze_font_sizes(self, text_blocks: List[Dict[str, Any]]) -> None:
        """
        Analyze font sizes in text blocks to determine categories vs items.
        Sets max_font_size (categories) and most_common_font_size (items).

        Args:
            text_blocks: List of text blocks from parser
        """
        # Collect all font sizes
        sizes = [block.get('size', 0) for block in text_blocks if block.get('size', 0) > 0]

        if not sizes:
            return

        # Find max font size (categories)
        self.max_font_size = max(sizes)

        # Find most common font size (items)
        size_counts = Counter(sizes)
        self.most_common_font_size = size_counts.most_common(1)[0][0]

    def _is_category_by_font(self, block: Dict[str, Any]) -> bool:
        """
        Check if block is a category based on font size.

        Args:
            block: Text block

        Returns:
            True if block has the largest font size (category)
        """
        size = block.get('size', 0)
        return size > 0 and size == self.max_font_size

    def should_stop_description(self, current_block: Dict[str, Any], previous_block: Optional[Dict[str, Any]]) -> bool:
        """
        Determine if description should stop based on gap and font changes.

        Args:
            current_block: Current text block
            previous_block: Previous text block

        Returns:
            True if description should stop
        """
        if not previous_block:
            return False

        current_text = current_block.get('text', '').strip()

        # Don't stop for price-only blocks - they should attach to current dish
        if self._contains_price(current_text) and len(current_text) <= 4:
            return False

        # Gap detection - large vertical gap indicates new section
        y_gap = current_block['top'] - previous_block.get('bottom', 0)
        if y_gap > self.GAP_THRESHOLD:
            return True

        # Font change detection - stop if font gets LARGER (new item)
        # Allow same or smaller fonts (descriptions can continue)
        if 'size' in current_block and 'size' in previous_block:
            current_size = current_block.get('size', 0)
            previous_size = previous_block.get('size', 0)

            # Only stop if current font is LARGER (changed from >=)
            if current_size > previous_size:
                return True

        return False

    def _is_subitem(self, text: str) -> bool:
        """
        Check if text is a sub-item (e.g., "6 WINGS", "12 WINGS").

        Args:
            text: Text to check

        Returns:
            True if text matches sub-item pattern
        """
        return bool(self.SUBITEM_PATTERN.match(text))

    def _is_subcategory(self, text: str) -> bool:
        """
        Check if text is a subcategory (looks like a category but smaller font).
        Subcategories are all caps, no price, but not in main CATEGORY_KEYWORDS list.

        Args:
            text: Text to check

        Returns:
            True if text is a subcategory
        """
        # Must be all caps
        if not text.isupper():
            return False

        # Must not have a price
        if self._contains_price(text):
            return False

        # Must match section pattern
        if not self.SECTION_PATTERN.match(text):
            return False

        # If it's in CATEGORY_KEYWORDS, it's a main category, not subcategory
        for keyword in self.CATEGORY_KEYWORDS:
            if keyword in text:
                return False

        # If it's 2-5 words and all caps, likely a subcategory
        word_count = len(text.split())
        if 2 <= word_count <= 5:
            return True

        return False

    def split_multi_category_header(self, text: str) -> List[str]:
        """
        Split headers containing multiple categories using semantic analysis.

        Args:
            text: Header text to split

        Returns:
            List of category headers (1 if no split needed, 2+ if split)
        """
        # Find all keyword positions
        keyword_positions = []
        for keyword in self.CATEGORY_KEYWORDS:
            if keyword in text:
                pos = text.find(keyword)
                keyword_end = pos + len(keyword)
                keyword_positions.append((pos, keyword_end, keyword))

        # If multiple keywords found, split between them
        if len(keyword_positions) > 1:
            # Sort by position
            keyword_positions.sort()

            # Split after the first keyword ends
            split_pos = keyword_positions[0][1]

            header1 = text[:split_pos].strip()
            header2 = text[split_pos:].strip()

            return [header1, header2]

        return [text]

    def _is_item_without_price(self, text: str) -> bool:
        """
        Detect items without prices using pattern matching.

        Args:
            text: Text to check

        Returns:
            True if text is an item without price
        """
        # First check: must NOT contain a price
        if self._contains_price(text):
            return False

        # All caps, reasonable length
        if text.isupper() and len(text) < 60:
            word_count = len(text.split())

            # Accept 2+ words
            if word_count >= 2:
                return True

            # Accept single words (3+ chars): COLESLAW, DILLINOIS, MESQUITE, BUFFALO, CAJUN
            if word_count == 1 and len(text) >= 3:
                return True

            # Accept very short items like "B&T"
            if word_count == 1 and 2 <= len(text) < 3 and '&' in text:
                return True

        # Number + CATEGORY pattern (e.g., "6 WINGS", "3 TENDERS")
        for keyword in self.CATEGORY_KEYWORDS:
            if re.match(rf'^\d+\s+{keyword}', text):
                return True

        return False

    def normalize_dishes(self, text_blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Normalize text blocks into structured dish data.

        Args:
            text_blocks: List of text blocks from parser

        Returns:
            List of normalized dish dictionaries
        """
        # First pass: analyze font sizes to determine categories vs items
        self._analyze_font_sizes(text_blocks)

        dishes = []
        current_dish = None
        previous_block = None
        pending_categories = []  # Queue for multi-category headers
        items_in_current_category = 0  # Track items added to current category

        for i, block in enumerate(text_blocks):
            text = block['text'].strip()

            if not text:
                continue

            # Check if should stop current description (gap or font change)
            if current_dish and self.should_stop_description(block, previous_block):
                dishes.append(current_dish)
                current_dish = None

            # Check if this is a section header
            if self._is_section_header(text, block):
                # Save current dish before changing category
                if current_dish:
                    dishes.append(current_dish)
                    current_dish = None

                # Reset subcategories when entering new category
                self.subcategories = {}

                # If we have a current category with no items, and we're seeing another header,
                # this means we have consecutive headers (multi-category situation)
                # Add current category to pending queue before processing new header
                if self.current_category and items_in_current_category == 0 and not pending_categories:
                    pending_categories.append(self.current_category)

                # Handle multi-category headers (single block with multiple categories)
                headers = self.split_multi_category_header(text)
                if len(headers) > 1:
                    # Multiple categories in one block - set first one, queue the rest
                    self.current_category = self._normalize_text(headers[0])
                    for header in headers[1:]:
                        pending_categories.append(self._normalize_text(header))
                    items_in_current_category = 0
                else:
                    # Single category header
                    self.current_category = self._normalize_text(text)
                    items_in_current_category = 0

                previous_block = block
                continue

            # Check if this is a price-only block (should attach to previous item)
            if self._contains_price(text) and len(text) <= 4:
                # This is just a price - attach to current dish if exists
                # Skip if it's a placeholder ($X) - leave price as None
                if current_dish and current_dish['price'] is None:
                    if text != '$X' and not self.PRICE_PLACEHOLDER_PATTERN.match(text):
                        current_dish['price'] = text
                previous_block = block
                continue

            # Check if this could be a subcategory (all caps, no price, not a category)
            # A subcategory:
            # 1. Has NO price (no placeholder, no real price)
            # 2. Has sub-items with number pattern below it (e.g., "6 WINGS")
            # 3. OR has items below with prices (real or placeholder)
            if (text.isupper() and not self._contains_price(text) and
                not self._is_category_by_font(block) and
                not self._is_subitem(text) and  # Sub-items are not subcategories
                len(text.split()) >= 2):
                # Check if there's a price on the same line (this is a regular item, not subcategory)
                current_y = block.get('top', 0)
                current_x = block.get('x0', 0)
                current_size = block.get('size', 0)

                has_price_on_same_line = False
                for j in range(i + 1, min(i + 5, len(text_blocks))):
                    next_block = text_blocks[j]
                    next_text = next_block['text'].strip()
                    next_y = next_block.get('top', 0)

                    # Check if on same line
                    if abs(next_y - current_y) < 3:
                        if self._contains_price(next_text):
                            has_price_on_same_line = True
                            break
                    else:
                        # Different line, stop checking
                        break

                # If has price on same line, this is NOT a subcategory - skip subcategory detection
                is_subcategory = False
                if not has_price_on_same_line:
                    # Look ahead to check for sub-items or items with prices
                    for j in range(i + 1, min(i + 15, len(text_blocks))):  # Check up to 15 blocks ahead
                        next_block = text_blocks[j]
                        next_text = next_block['text'].strip()
                        next_y = next_block.get('top', 0)
                        next_x = next_block.get('x0', 0)
                        next_size = next_block.get('size', 0)

                        # Skip blocks on the same line (same y-coordinate)
                        if abs(next_y - current_y) < 3:  # 3 pixel tolerance
                            continue

                        # Check if this next block is in the same column (similar x-coordinate)
                        if abs(next_x - current_x) < 30:  # 30 pixel tolerance
                            # Found a block in same column on different line
                            # Check if it's a sub-item (number pattern)
                            if self._is_subitem(next_text):
                                is_subcategory = True
                                break
                            # OR check if it has smaller font size AND current is larger than most common
                            # (to avoid treating regular items with descriptions as subcategories)
                            elif (next_size > 0 and current_size > 0 and
                                  next_size < current_size and
                                  current_size > self.most_common_font_size):
                                is_subcategory = True
                                break
                            # If same or larger size and not a sub-item, stop looking
                            elif next_size >= current_size and not self._contains_price(next_text):
                                break

                if is_subcategory:
                    # This is a subcategory - store it by x-coordinate
                    x_pos = block.get('x0', 0)

                    # If this subcategory has larger font than most common,
                    # clear subcategories appropriately
                    if current_size > self.most_common_font_size:
                        # If this is a cross-column subcategory, clear ALL subcategories
                        # (since it will match items in multiple columns)
                        if text in self.CROSS_COLUMN_SUBCATEGORIES:
                            self.subcategories = {}
                        else:
                            # Otherwise, only clear subcategories at this x-position
                            keys_to_remove = [k for k in self.subcategories.keys() if abs(k - x_pos) < 30]
                            for k in keys_to_remove:
                                del self.subcategories[k]

                    self.subcategories[x_pos] = text
                    previous_block = block
                    continue

            # Check if this is a sub-item (number + word pattern)
            if self._is_subitem(text):
                # Find matching subcategory by x-coordinate
                current_x = block.get('x0', 0)
                matching_subcategory = None

                # Find the closest subcategory by x-coordinate
                for subcat_x, subcat_name in self.subcategories.items():
                    # Use larger tolerance for cross-column subcategories
                    tolerance = 200 if subcat_name in self.CROSS_COLUMN_SUBCATEGORIES else 30

                    if abs(current_x - subcat_x) < tolerance:
                        matching_subcategory = subcat_name
                        break

                # Save previous dish if exists
                if current_dish:
                    dishes.append(current_dish)

                # Create dish with or without subcategory
                if matching_subcategory:
                    dish_name = f"{matching_subcategory} ({text})"
                else:
                    dish_name = text

                current_dish = {
                    'category': self.current_category,
                    'dish_name': self._normalize_text(dish_name),
                    'price': None,
                    'description': ''
                }
                items_in_current_category += 1

                previous_block = block
                continue

            # Check if this line contains a dish name and price
            if self._contains_price(text):
                # If we have pending categories and current category has items,
                # move to next pending category
                if pending_categories and items_in_current_category > 0:
                    self.current_category = pending_categories.pop(0)
                    items_in_current_category = 0
                    self.subcategories = {}  # Reset subcategories for new category

                # Save previous dish if exists
                if current_dish:
                    dishes.append(current_dish)

                # Clear subcategories when we hit a regular priced item
                self.subcategories = {}

                # Start new dish
                current_dish = self._parse_dish_line(text)
                items_in_current_category += 1
            # Check if this is an item without price
            elif self._is_item_without_price(text):
                # If we have pending categories and haven't added items yet,
                # move to next pending category (this is the first item for that category)
                if pending_categories and items_in_current_category == 0:
                    self.current_category = pending_categories.pop(0)
                # If we have pending categories and current category has items,
                # move to next pending category
                elif pending_categories and items_in_current_category > 0:
                    self.current_category = pending_categories.pop(0)
                    items_in_current_category = 0
                    self.subcategories = {}  # Reset subcategories for new category

                # Save previous dish if exists
                if current_dish:
                    dishes.append(current_dish)

                # Find matching subcategory by x-coordinate and check font size
                current_x = block.get('x0', 0)
                current_size = block.get('size', 0)
                matching_subcategory = None

                for subcat_x, subcat_name in self.subcategories.items():
                    # Use larger tolerance for cross-column subcategories
                    tolerance = 200 if subcat_name in self.CROSS_COLUMN_SUBCATEGORIES else 30

                    if abs(current_x - subcat_x) < tolerance:
                        matching_subcategory = subcat_name
                        break

                # Create dish name with or without subcategory
                if matching_subcategory:
                    dish_name = f"{matching_subcategory} ({text})"
                else:
                    dish_name = text

                # Create item with null price
                current_dish = {
                    'category': self.current_category,
                    'dish_name': self._normalize_text(dish_name),
                    'price': None,
                    'description': ''
                }
                items_in_current_category += 1
            elif current_dish:
                # Append as description
                current_dish['description'] = self._append_description(
                    current_dish.get('description', ''),
                    text
                )

            previous_block = block

        # Add last dish
        if current_dish:
            dishes.append(current_dish)

        return dishes

    def _is_section_header(self, text: str, block: Dict[str, Any]) -> bool:
        """
        Check if text is a section header based on font size.

        Args:
            text: Text to check
            block: Text block with font metadata

        Returns:
            True if text is a section header (largest font size)
        """
        # Section headers have the largest font size
        return self._is_category_by_font(block)

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
        # Check for price placeholder first
        if self.PRICE_PLACEHOLDER_PATTERN.search(text):
            price = None  # Use null for placeholders
            # Remove $X from text for dish name extraction
            dish_name = self.PRICE_PLACEHOLDER_PATTERN.sub('', text).strip()
        else:
            # Extract regular price
            price_match = self.PRICE_PATTERN.search(text)
            price = price_match.group(0) if price_match else None

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

    def clean_dish_names(self, dishes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Clean dish names by removing placeholders and extra whitespace.

        Args:
            dishes: List of dish dictionaries

        Returns:
            List of dishes with cleaned dish names
        """
        for dish in dishes:
            name = dish['dish_name']

            # Remove $X placeholders
            name = re.sub(r'\$X\s*', '', name)

            # Trim extra whitespace
            name = ' '.join(name.split())

            dish['dish_name'] = name.strip()

        return dishes

    def filter_non_menu_items(self, dishes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter out non-menu items using case-based detection.

        Args:
            dishes: List of dish dictionaries

        Returns:
            Filtered list of dishes
        """
        filtered = []
        for dish in dishes:
            name = dish['dish_name']

            if not name:
                continue

            # Skip if starts with lowercase (instructional text)
            if name[0].islower():
                continue

            # Skip if contains '+$' (modifier, not dish)
            if '+$' in name:
                continue

            filtered.append(dish)

        return filtered

    def _split_parenthetical_items(self, dish_name: str) -> List[str]:
        """
        Split dish names with parenthetical text into separate items.

        Args:
            dish_name: Dish name to check

        Returns:
            List of dish names (split if parenthetical, otherwise original)
        """
        match = re.match(r'^(.+?)\s*\((.+?)\)$', dish_name)

        if match:
            main_item = match.group(1).strip()
            paren_item = match.group(2).strip()

            # Keep if main item is a known subcategory
            KNOWN_SUBCATEGORIES = ['SIGNATURE SAUCES', 'FLIGHTS', 'JUMBO CHICKEN WINGS',
                                   'BREADED CHICKEN TENDERS']
            if main_item in KNOWN_SUBCATEGORIES:
                return [dish_name]

            # Keep if parenthetical is a number pattern (e.g., "6 WINGS")
            if re.match(r'^\d+\s+\w+', paren_item):
                return [dish_name]

            # Keep if parenthetical is a single word (flavor/variant, not a separate dish)
            # e.g., "RED BULL RED EDITION (WATERMELON)" should stay together
            if len(paren_item.split()) == 1:
                return [dish_name]

            # Otherwise split
            return [main_item, paren_item]

        return [dish_name]

    def split_parenthetical_dishes(self, dishes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Split dishes with parenthetical text into separate dishes.

        For items like "MAIN ITEM (VARIANT)", if MAIN ITEM appears multiple times
        with different variants, only keep the parenthetical parts to avoid duplicates.

        Args:
            dishes: List of dish dictionaries

        Returns:
            List of dishes with parenthetical items split
        """
        # First pass: identify main items that appear multiple times with parentheticals
        main_item_counts = {}
        for dish in dishes:
            match = re.match(r'^(.+?)\s*\((.+?)\)$', dish['dish_name'])
            if match:
                main_item = match.group(1).strip()
                paren_item = match.group(2).strip()

                # Only count if it would be split (multi-word parenthetical, not a subcategory)
                KNOWN_SUBCATEGORIES = ['SIGNATURE SAUCES', 'FLIGHTS', 'JUMBO CHICKEN WINGS',
                                       'BREADED CHICKEN TENDERS']
                if (main_item not in KNOWN_SUBCATEGORIES and
                    not re.match(r'^\d+\s+\w+', paren_item) and
                    len(paren_item.split()) > 1):
                    main_item_counts[main_item] = main_item_counts.get(main_item, 0) + 1

        # Second pass: split dishes
        result = []
        for dish in dishes:
            dish_names = self._split_parenthetical_items(dish['dish_name'])

            if len(dish_names) > 1:
                main_item = dish_names[0]
                paren_item = dish_names[1]

                # If main item appears multiple times with parentheticals, only keep parenthetical
                if main_item in main_item_counts and main_item_counts[main_item] > 1:
                    result.append({
                        'category': dish['category'],
                        'dish_name': paren_item,
                        'price': dish['price'],
                        'description': dish['description']
                    })
                else:
                    # Otherwise keep both
                    for name in dish_names:
                        result.append({
                            'category': dish['category'],
                            'dish_name': name,
                            'price': dish['price'],
                            'description': dish['description']
                        })
            else:
                result.append(dish)

        return result
