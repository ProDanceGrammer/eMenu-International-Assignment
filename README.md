# Menu Extractor - Restaurant Menu PDF Parser

A Python application that extracts and normalizes restaurant menu data from PDF files, outputting structured JSON data.

## Features

- **Two-Column Layout Support** - Intelligently separates and processes two-column menu layouts
- **Robust Price Parsing** - Handles prices at beginning or end of lines, plus missing prices and placeholders
- **Multi-line Description Merging** - Automatically combines descriptions that span multiple lines
- **Data Normalization** - Cleans whitespace, formats text consistently
- **Sequential ID Generation** - Assigns unique sequential IDs (001, 002, 003...)
- **Type-Safe Null Handling** - Uses JSON `null` for missing prices (not strings)

## Requirements

- Python 3.12 or higher
- pdfplumber
- pytest (for testing)

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
python -m src.menu_extractor.extractor
```

This will:
- Parse `data/espn_bet.pdf`
- Extract all dishes with categories, names, prices, and descriptions
- Save output to `output/menu_data.json`

### Custom Paths

Specify custom input/output paths:
```bash
python -m src.menu_extractor.extractor <pdf_path> <output_path>
```

Example:
```bash
python -m src.menu_extractor.extractor data/my_menu.pdf output/my_output.json
```

## Output Format

Each dish is structured as:
```json
{
  "category": "BURGERS",
  "dish_name": "ALL AMERICAN BURGER",
  "price": "$17",
  "description": "7 oz. steakburger, choice of cheese, lettuce, tomato, onion, pickles, brioche bun",
  "dish_id": "001"
}
```

**Note:** Items without prices (e.g., sauces, sides) have `price: null` instead of a string value.

## Running Tests

Run the test suite:
```bash
pytest tests/test_extractor.py -v
```

Tests validate:
- Extraction correctness and coverage
- Data structure integrity
- Sequential ID generation
- Price formatting
- Null price handling
- JSON output validity

## Architecture

### Package Structure
```
src/menu_extractor/
  ├── parser.py       # PDF parsing with pdfplumber
  ├── normalizer.py   # Data cleaning and structuring
  └── extractor.py    # Main orchestration
```

### Key Design Decisions

#### 1. Two-Column Layout Processing

**Why:** Restaurant menus often use two-column layouts. Processing line-by-line without column separation mixes content from both columns, resulting in incorrect dish associations.

**How:** The parser separates words into left and right columns based on x-coordinates before grouping into lines. Each column is then processed independently, maintaining proper dish-to-description relationships.

#### 2. Null for Missing Prices

**Why `null` instead of strings like `"N/A"` or `"$X"`:**

- **Type Consistency** - Maintains price as numeric type (or nullable numeric), not mixed string/number
- **ML/Data Processing** - Consistent types prevent errors in data pipelines and model training
- **Database Standard** - SQL databases use `NULL` for missing values
- **Semantic Clarity** - `null` explicitly means "no value", not ambiguous text
- **Easy Filtering** - Simple queries like `WHERE price IS NOT NULL` work naturally
- **Downstream Compatibility** - Pandas/NumPy handle `null` → `NaN` automatically

#### 3. Single JSON File Output

**Why single file instead of multiple files:**

- **Ease of Implementation** - One write operation, simpler error handling
- **Ease of Use** - Single `json.load()` call to get all data
- **Performance** - Menus typically have 50-200 dishes (~50-200KB), loading is instant
- **Data Integrity** - Atomic operation, no risk of partial data
- **Simplicity** - Easier to share, version control, and backup

#### 4. Package Structure for Small Script

**Why organized structure even for a small script:**

- **Separation of Concerns** - Each module has single responsibility (parser, normalizer, orchestrator)
- **Easier to Read** - Clear file names, no scrolling through monolithic script
- **Easier to Maintain** - Changes are isolated, reducing risk of breaking other parts
- **Easier to Test** - Can test each module independently
- **Scalable Foundation** - Structure supports growth without refactoring
- **Professional Standard** - Shows engineering maturity

## Project Structure

```
eMenu-International-Assignment/
├── src/
│   └── menu_extractor/
│       ├── __init__.py
│       ├── parser.py          # PDF parsing logic
│       ├── normalizer.py      # Data normalization
│       └── extractor.py       # Main orchestration
├── tests/
│   └── test_extractor.py      # Integration tests
├── data/
│   └── espn_bet.pdf           # Input menu PDF
├── output/
│   └── menu_data.json         # Extracted JSON output
├── experiments/               # PDF library comparison
├── requirements.txt
├── README.md
└── CLAUDE.md
```

## Known Limitations

- Assumes two-column layout (can be extended for other layouts)
- Section headers must be all uppercase
- Prices must contain `$` symbol
- Multi-page menus are supported but tested primarily on 2-page menu

## Next Steps

Potential enhancements:
- Support for single-column layouts
- CLI arguments for configuration (column detection threshold, output format)
- Support for additional output formats (CSV, Excel)
- Allergen information extraction
- Image/logo detection and extraction
- Support for menus with more complex layouts (3+ columns, mixed layouts)

## License

This project was created as a technical assignment for eMenu International.

## Author

Created with assistance from Claude Code (Anthropic).
