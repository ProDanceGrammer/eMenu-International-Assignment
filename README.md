# Menu Extractor - Restaurant Menu PDF Parser

A Python application that extracts and normalizes restaurant menu data from PDF files using coordinate-based text analysis, outputting structured JSON data.

## Features

- **Coordinate-Based Text Analysis** - Uses word positions and spatial relationships to understand menu structure
- **Intelligent Phrase Detection** - Groups words into phrases based on proximity and alignment
- **Category & Subcategory Recognition** - Identifies hierarchical menu structure using font sizes
- **Price Detection** - Handles both numeric prices ($17) and placeholders ($X)
- **Description Allocation** - Automatically associates descriptions with menu items based on spatial proximity
- **Multi-Column Layout Support** - Processes complex two-column menu layouts
- **Neighbor Analysis** - Tracks spatial relationships (left, right, above, below) between words
- **Type-Safe Null Handling** - Uses JSON `null` for missing prices

## Requirements

- Python 3.12 or higher
- pdfplumber

## Installation

1. Clone the repository:
```bash
git clone https://github.com/ProDanceGrammer/eMenu-International-Assignment.git
cd eMenu-International-Assignment
```

2. Create and activate virtual environment:
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Unix/Mac
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

Extract menu from the default PDF:
```bash
python main.py
```

This will:
- Parse `data/espn_bet.pdf` (first 2 pages)
- Extract all dishes with categories, names, prices, and descriptions
- Save output to `output/menu_data.json`

### Customization

To process different pages or PDFs, modify the constants in `main.py`:
```python
MENU_PATH = 'data/espn_bet.pdf'  # Input PDF path
OUTPUT_PATH = 'output/menu_data.json'  # Output JSON path
```

To process different pages, modify the range in the main block:
```python
for i in range(2):  # Change range to process different pages
    ordered_output.extend(words_analysis(MENU_PATH, page_num=i))
```

## Output Format

Each dish is structured as:
```json
{
    "category": "BURGERS",
    "dish_name": "ALL AMERICAN BURGER",
    "price": "$17",
    "description": "7 oz. steakburger, choice of cheese, lettuce, tomato, onion, pickles, brioche bun",
    "dish_id": 0
}
```

For items with subcategories:
```json
{
    "category": "AIN'T NO THING BUT A CHICKEN...",
    "dish_name": "JUMBO CHICKEN WINGS (6 WINGS)",
    "price": "$12",
    "description": "",
    "dish_id": 10
}
```

**Note:** Items without prices have `price: null` instead of a string value.

## How It Works

The extraction process follows these steps:

1. **Word Extraction** - Extract all words from PDF with coordinates (x0, x1, top, bottom)
2. **Neighbor Analysis** - Calculate spatial relationships between words (left, right, above, below neighbors)
3. **Font Size Analysis** - Identify category and subcategory font sizes
4. **Phrase Formation** - Group words into phrases based on proximity and alignment
5. **Classification** - Classify phrases as categories, items, descriptions, or prices
6. **Category Assignment** - Associate items with their parent categories using spatial distance
7. **Description Allocation** - Match descriptions to items based on proximity
8. **Price Allocation** - Link prices to items using right-neighbor relationships
9. **Subcategory Detection** - Identify subcategories and their sub-items
10. **Ordering** - Sort output by category and item coordinates
11. **JSON Output** - Generate structured JSON with sequential dish IDs

## Architecture

### Core Classes

#### `Word`
Represents a single word with:
- Text content and coordinates (x0, x1, top, bottom, height)
- Neighbor references (left, right, above, below)
- Price detection (numeric price vs placeholder)
- Phrase membership tracking

#### `Phrase`
Represents a group of words forming a logical unit:
- Collection of Word objects
- Type classification (category, item, subcategory, description, price)
- Relationships to other phrases (category, subcategory, description, price)
- Spatial properties (x0, x1, min_y, max_y, height range)

### Key Design Decisions

#### 1. Coordinate-Based Spatial Analysis

**Why:** Traditional line-by-line parsing fails with complex layouts. Spatial relationships between words reveal menu structure more reliably than text patterns alone.

**How:** 
- Calculate distances between all word pairs
- Track nearest neighbors in all four directions
- Use Euclidean distance to determine phrase relationships
- Apply thresholds for same-line detection and phrase grouping

#### 2. Font Size for Hierarchy Detection

**Why:** Categories and subcategories are visually distinguished by font size in most menus.

**How:**
- Analyze all font sizes in the document
- Largest size = categories
- Second largest = subcategories
- Smaller sizes = items and descriptions

#### 3. Neighbor-Based Phrase Formation

**Why:** Words that are close together horizontally or vertically aligned form logical phrases.

**How:**
- Start with each word as a potential phrase
- Extend phrase to right neighbor if distance < 10 pixels
- If no close right neighbor, check for aligned word below
- Stop at price words (they're separate phrases)

#### 4. Distance-Based Item Assignment

**Why:** Items belong to the closest category/subcategory that's above and to the left.

**How:**
- Calculate Euclidean distance from item to each category
- Check that item is below and right-aligned with category
- Assign to closest valid category
- Prevent items from being assigned to multiple categories

## Project Structure

```
Menu-Parser/
├── main.py                    # Main extraction logic
├── data/
│   └── espn_bet.pdf           # Input menu PDF
├── output/
│   ├── menu_data.json         # Extracted JSON output
│   └── expected_menu_data.json # Expected output for validation
├── requirements.txt
├── README.md
└── .gitignore
```

## Configuration Constants

Key constants that can be adjusted in `main.py`:

```python
WHITESPACE_PIXELS_DISTANCE = 10        # Max distance to group words in a phrase
SHORT_NEW_LINE_PIXELS_DIFFERENCE = 10  # Max distance for multi-line phrases
SAME_LINE_THRESHOLD = 5                # Tolerance for same-line detection
MAIN_COLUMN_LENGTH = 190               # Column width for category assignment
MAX_DESCRIPTION_LENGTH = 400           # Max width for description phrases
PAGE_PIXELS_LENGTH = 1100              # Page height for coordinate conversion
```

## Known Limitations

- Items must be uppercase to be detected (coupled with uppercase logic)
- Assumes specific font size hierarchy (largest = category, second = subcategory)
- Prices must contain `$` symbol
- Price must be right neighbor of item (no intervening words)
- Tested primarily on 2-page ESPN Bet menu

## Nice to Add in the Future

1. **Decouple from uppercase logic** - Support menus where items aren't all uppercase
2. **Replace typing with composition** - Use proper class inheritance instead of type strings
3. **Improve subcategory sorting** - Better ordering when subcategories are present
4. **Configurable thresholds** - CLI arguments for distance thresholds and layout parameters
5. **Support for more layouts** - Single-column, 3+ columns, mixed layouts
6. **Better price detection** - Handle prices not directly adjacent to items
7. **Allergen information extraction** - Detect and extract allergen markers
8. **Multi-language support** - Handle non-English menus with different character sets
9. **Confidence scores** - Add confidence metrics for extracted data
10. **Visual debugging** - Generate annotated PDFs showing detected regions

## AI Tool Usage

This project was completed with AI assistance as part of the eMenu International technical assignment.

- **Tool Used**: Claude Code (Anthropic) for initial research, experimenting with PDF parsing libraries (PyPDF2, pdfplumber, PyMuPDF), and documentation generation
- **What Changed**: Transitioned from AI-generated solutions to hands-on coding when Claude started drifting from requirements. Implemented the coordinate-based spatial analysis and neighbor detection logic manually for better precision and control
- **Assumptions**: Items are uppercase, largest font = category, prices are right-adjacent to items
- **Edge Cases**: Subcategory sorting needs improvement; complex nested structures may not be fully handled
- **Known Gaps**: Tightly coupled to ESPN Bet menu layout; generalization to other menu formats requires additional work

## License

This project was created as a technical assignment for eMenu International.

## Author

Developed by ProDanceGrammer.
