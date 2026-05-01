# Software Engineering Plan: Menu Extraction System

**Project:** eMenu International Assignment - PDF Menu Data Extraction  
**Date:** 2026-05-01  
**Status:** Implementation Ready

---

## 1. Executive Summary

This document outlines the comprehensive software engineering plan for building a menu extraction system that processes PDF restaurant menus and outputs structured JSON data. The system will extract dish information including categories, names, prices, descriptions, and assign sequential IDs.

**Key Technical Decisions:**
- **PDF Library:** pdfplumber (chosen after comparative analysis)
- **Architecture:** Modular package structure with separation of concerns
- **Output Format:** Single JSON file with null for missing prices
- **Testing Strategy:** Integration tests against actual PDF (espn_bet.pdf)

---

## 2. Architecture Design

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Menu Extractor System                    │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐      ┌──────────────┐      ┌───────────┐ │
│  │   Parser     │ ───> │  Normalizer  │ ───> │  Output   │ │
│  │  (PDF → Raw) │      │ (Raw → Clean)│      │  (JSON)   │ │
│  └──────────────┘      └──────────────┘      └───────────┘ │
│         │                      │                     │       │
│         └──────────────────────┴─────────────────────┘       │
│                            │                                  │
│                    ┌───────▼────────┐                        │
│                    │   Extractor    │                        │
│                    │  (Orchestrator)│                        │
│                    └────────────────┘                        │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Module Responsibilities

#### **extractor.py** - Orchestration Layer
**Responsibility:** High-level coordination and business logic

**Key Functions:**
- `extract_menu(pdf_path: str, output_path: str) -> List[Dict]`
  - Main entry point
  - Coordinates parser and normalizer
  - Handles file I/O
  - Assigns sequential dish_id values
  - Writes final JSON output

**Design Principles:**
- Single Responsibility: Orchestration only
- Dependency Injection: Receives parser and normalizer instances
- Error handling at the boundary
- Logging for debugging

---

#### **parser.py** - PDF Parsing Layer
**Responsibility:** Extract raw text and structure from PDF

**Key Classes/Functions:**
- `PDFParser` class
  - `__init__(pdf_path: str)`
  - `extract_pages() -> List[PageData]`
  - `_extract_text_with_layout(page) -> str`
  - `_detect_columns(page) -> List[Column]`

**Data Structures:**
```python
@dataclass
class PageData:
    page_number: int
    text: str
    words: List[Word]  # With positioning data
    
@dataclass
class Word:
    text: str
    x0: float
    x1: float
    top: float
    bottom: float
```

**Key Challenges:**
- Two-column layout detection
- Preserving reading order (left column top-to-bottom, then right column)
- Handling multi-line descriptions

**Strategy:**
- Use pdfplumber's `extract_text()` for layout-aware extraction
- Use `extract_words()` for positioning data if needed
- Leverage pdfplumber's natural column handling (already tested in experiments)

---

#### **normalizer.py** - Data Cleaning & Structuring Layer
**Responsibility:** Transform raw text into structured dish data

**Key Classes/Functions:**
- `MenuNormalizer` class
  - `normalize(pages: List[PageData]) -> List[Dict]`
  - `_identify_categories(text: str) -> List[str]`
  - `_extract_dishes(text: str, category: str) -> List[RawDish]`
  - `_parse_dish_line(line: str) -> Optional[RawDish]`
  - `_merge_multiline_descriptions(dishes: List[RawDish]) -> List[RawDish]`
  - `_normalize_price(price_str: str) -> Optional[str]`
  - `_clean_text(text: str) -> str`

**Data Structures:**
```python
@dataclass
class RawDish:
    category: str
    dish_name: str
    price: Optional[str]  # "$17" or None
    description: str
    
# Output format (after dish_id assignment in extractor)
{
    "category": "BURGERS",
    "dish_name": "ALL AMERICAN BURGER",
    "price": "$17",  # or null
    "description": "7 oz. steakburger, choice of cheese...",
    "dish_id": "001"
}
```

**Normalization Rules:**
1. **Category Detection:**
   - All-caps lines without prices
   - Known patterns: "LEADING OFF", "BURGERS", "SALADS & SOUP", etc.
   - Store current category as state

2. **Dish Line Pattern:**
   - Format: `DISH NAME $PRICE` or `DISH NAME` (no price)
   - Dish names are typically all-caps or title case
   - Prices: `$XX` or `$X` (placeholder)
   - Handle missing prices → `null`

3. **Multi-line Description Merging:**
   - Lines after dish name (lowercase, no price) are descriptions
   - Continue until next dish or category
   - Join with single space
   - Trim whitespace

4. **Price Normalization:**
   - Keep format: `$17`, `$X`
   - Convert missing/empty to `null` (JSON null, not string)
   - Validate format with regex: `r'^\$\d+$'` or `r'^\$X$'`

5. **Text Cleaning:**
   - Strip leading/trailing whitespace
   - Normalize multiple spaces to single space
   - Remove special characters if needed
   - Preserve commas in descriptions

---

## 3. Data Flow

```
┌─────────────┐
│ espn_bet.pdf│
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────┐
│ Parser (parser.py)                      │
│ - Open PDF with pdfplumber              │
│ - Extract text preserving layout        │
│ - Handle two-column format              │
│ - Return List[PageData]                 │
└──────┬──────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────┐
│ Normalizer (normalizer.py)              │
│ - Identify category headers             │
│ - Parse dish lines (name + price)       │
│ - Merge multi-line descriptions         │
│ - Normalize prices (null for missing)   │
│ - Clean whitespace                      │
│ - Return List[RawDish]                  │
└──────┬──────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────┐
│ Extractor (extractor.py)                │
│ - Assign sequential dish_id (001, 002)  │
│ - Convert to final JSON structure       │
│ - Write to output/menu_data.json        │
└──────┬──────────────────────────────────┘
       │
       ▼
┌─────────────────┐
│ menu_data.json  │
│ [                │
│   {              │
│     "category": "BURGERS",              │
│     "dish_name": "ALL AMERICAN BURGER", │
│     "price": "$17",                     │
│     "description": "7 oz. steakburger...",│
│     "dish_id": "001"                    │
│   },             │
│   ...            │
│ ]                │
└─────────────────┘
```

---

## 4. Error Handling Strategy

### 4.1 Error Categories

**1. File System Errors**
- PDF not found
- Output directory not writable
- Permissions issues

**Strategy:** Fail fast with clear error messages

```python
try:
    with pdfplumber.open(pdf_path) as pdf:
        ...
except FileNotFoundError:
    raise FileNotFoundError(f"PDF not found: {pdf_path}")
except PermissionError:
    raise PermissionError(f"Cannot read PDF: {pdf_path}")
```

**2. PDF Parsing Errors**
- Corrupted PDF
- Encrypted PDF
- Unsupported format

**Strategy:** Catch and wrap with context

```python
try:
    pages = parser.extract_pages()
except Exception as e:
    raise RuntimeError(f"Failed to parse PDF: {e}") from e
```

**3. Data Extraction Errors**
- Unexpected format
- Missing expected patterns
- Malformed data

**Strategy:** Graceful degradation with logging

```python
def _parse_dish_line(line: str) -> Optional[RawDish]:
    try:
        # Parse logic
        return dish
    except Exception as e:
        logger.warning(f"Failed to parse line: {line!r} - {e}")
        return None  # Skip malformed lines
```

**4. Data Validation Errors**
- Invalid price format
- Empty dish name
- Missing required fields

**Strategy:** Log warnings, use defaults

```python
if not dish_name.strip():
    logger.warning(f"Empty dish name in category {category}")
    continue  # Skip invalid dishes
```

### 4.2 Logging Strategy

```python
import logging

# Configure in extractor.py
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Usage
logger.info(f"Processing PDF: {pdf_path}")
logger.warning(f"No price found for dish: {dish_name}")
logger.error(f"Failed to parse page {page_num}: {e}")
```

---

## 5. Testing Approach

### 5.1 Test Structure

```
tests/
├── __init__.py
├── test_extractor.py      # Integration tests
├── test_parser.py         # Unit tests for parser
├── test_normalizer.py     # Unit tests for normalizer
└── fixtures/
    └── expected_output.json  # Expected results for validation
```

### 5.2 Test Categories

#### **Integration Tests (test_extractor.py)**
Test the full pipeline against actual PDF

```python
def test_extract_menu_full_pipeline():
    """Test complete extraction from espn_bet.pdf"""
    pdf_path = "data/espn_bet.pdf"
    output_path = "output/menu_data.json"
    
    result = extract_menu(pdf_path, output_path)
    
    # Assertions
    assert len(result) > 0
    assert all('dish_id' in dish for dish in result)
    assert all('category' in dish for dish in result)
    assert result[0]['dish_id'] == '001'
    assert result[1]['dish_id'] == '002'

def test_price_handling():
    """Test null for missing prices and $X placeholders"""
    result = extract_menu("data/espn_bet.pdf", "output/test.json")
    
    # Find dishes without prices
    no_price_dishes = [d for d in result if d['price'] is None]
    assert len(no_price_dishes) > 0  # Should have some
    
    # Find dishes with $X placeholder
    placeholder_dishes = [d for d in result if d['price'] == '$X']
    assert len(placeholder_dishes) > 0  # Should have some

def test_multiline_descriptions():
    """Test that multi-line descriptions are merged"""
    result = extract_menu("data/espn_bet.pdf", "output/test.json")
    
    # Find "ALL AMERICAN BURGER"
    burger = next(d for d in result if 'ALL AMERICAN' in d['dish_name'])
    
    # Description should be complete
    assert 'steakburger' in burger['description']
    assert 'brioche bun' in burger['description']
    assert '\n' not in burger['description']  # No newlines

def test_sequential_dish_ids():
    """Test dish_id numbering is sequential"""
    result = extract_menu("data/espn_bet.pdf", "output/test.json")
    
    dish_ids = [d['dish_id'] for d in result]
    expected_ids = [f"{i:03d}" for i in range(1, len(result) + 1)]
    
    assert dish_ids == expected_ids
```

#### **Unit Tests (test_parser.py)**

```python
def test_pdf_parser_initialization():
    """Test PDFParser can open PDF"""
    parser = PDFParser("data/espn_bet.pdf")
    assert parser is not None

def test_extract_pages():
    """Test page extraction returns correct structure"""
    parser = PDFParser("data/espn_bet.pdf")
    pages = parser.extract_pages()
    
    assert len(pages) == 2  # espn_bet.pdf has 2 pages
    assert all(isinstance(p, PageData) for p in pages)
    assert all(p.text for p in pages)  # All pages have text
```

#### **Unit Tests (test_normalizer.py)**

```python
def test_identify_categories():
    """Test category header detection"""
    text = "LEADING OFF\nJUMBO PRETZEL $16\nBURGERS\nALL AMERICAN $17"
    normalizer = MenuNormalizer()
    categories = normalizer._identify_categories(text)
    
    assert "LEADING OFF" in categories
    assert "BURGERS" in categories

def test_parse_dish_with_price():
    """Test parsing dish line with price"""
    line = "ALL AMERICAN BURGER $17"
    normalizer = MenuNormalizer()
    dish = normalizer._parse_dish_line(line, "BURGERS")
    
    assert dish.dish_name == "ALL AMERICAN BURGER"
    assert dish.price == "$17"
    assert dish.category == "BURGERS"

def test_parse_dish_without_price():
    """Test parsing dish line without price"""
    line = "SIGNATURE SAUCES"
    normalizer = MenuNormalizer()
    dish = normalizer._parse_dish_line(line, "SIDES")
    
    assert dish.dish_name == "SIGNATURE SAUCES"
    assert dish.price is None

def test_normalize_price():
    """Test price normalization"""
    normalizer = MenuNormalizer()
    
    assert normalizer._normalize_price("$17") == "$17"
    assert normalizer._normalize_price("$X") == "$X"
    assert normalizer._normalize_price("") is None
    assert normalizer._normalize_price(None) is None

def test_clean_text():
    """Test text cleaning"""
    normalizer = MenuNormalizer()
    
    assert normalizer._clean_text("  extra  spaces  ") == "extra spaces"
    assert normalizer._clean_text("line1\nline2") == "line1 line2"
```

### 5.3 Test Execution

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src/menu_extractor --cov-report=html

# Run specific test file
pytest tests/test_extractor.py -v

# Run specific test
pytest tests/test_extractor.py::test_extract_menu_full_pipeline -v
```

### 5.4 Test Data Strategy

**Primary Test Data:** `data/espn_bet.pdf` (actual assignment PDF)

**Why not mock data?**
- Real-world validation
- Catches actual PDF quirks
- Simpler test setup
- Matches evaluation criteria

**Edge Cases to Verify:**
- Dishes without prices (sauces section)
- Price placeholders ($X in drinks section)
- Multi-line descriptions (most dishes)
- Two-column layout (entire PDF)
- Special characters in descriptions
- Various category formats

---

## 6. Implementation Steps

### Phase 1: Project Setup (15 min)
1. Create directory structure
2. Set up `__init__.py` files
3. Update `requirements.txt` with dependencies
4. Create test directory structure

### Phase 2: Parser Implementation (45 min)
1. Implement `PDFParser` class
2. Add `extract_pages()` method
3. Test with espn_bet.pdf
4. Verify text extraction quality
5. Write unit tests for parser

### Phase 3: Normalizer Implementation (60 min)
1. Implement `MenuNormalizer` class
2. Add category detection logic
3. Add dish line parsing with regex
4. Implement multi-line description merging
5. Add price normalization
6. Add text cleaning utilities
7. Write unit tests for normalizer

### Phase 4: Extractor Implementation (30 min)
1. Implement `extract_menu()` orchestration
2. Add dish_id assignment logic
3. Add JSON output writing
4. Add error handling and logging
5. Write integration tests

### Phase 5: Testing & Validation (30 min)
1. Run full test suite
2. Manually inspect output JSON
3. Verify against requirements:
   - All dishes extracted
   - Multi-line descriptions merged
   - Prices handled correctly (null for missing)
   - Sequential dish_id numbering
   - Single JSON file output
4. Fix any issues found

### Phase 6: Documentation (30 min)
1. Write README.md with:
   - Setup instructions
   - Usage examples
   - Design decisions
   - Next steps
2. Update AI_USAGE_REFLECTION.md with:
   - Where Claude Code was used
   - What was adapted and why
   - Assumptions and edge cases
   - Known limitations

**Total Estimated Time:** ~3.5 hours

---

## 7. Design Decisions & Rationale

### 7.1 Why pdfplumber?

**Decision:** Use pdfplumber for PDF extraction

**Rationale:**
- Excellent two-column layout preservation (verified in experiments)
- Prices appear on same line as dish names (easier parsing)
- Good balance of simplicity and power
- Table detection capability (bonus feature)
- Word-level positioning available if needed

**Alternatives Considered:**
- PyPDF2: Poor layout preservation
- PyMuPDF: Prices separated from dish names (more complex parsing)
- pdfminer.six: Overly complex for this use case

**Evidence:** See `experiments/COMPARISON.md`

### 7.2 Why null for Missing Prices?

**Decision:** Use JSON `null` (not string "null" or empty string)

**Rationale:**
- **Type consistency:** Distinguishes "no price" from "$0" or empty string
- **Database standard:** SQL NULL semantics
- **ML-friendly:** Easy to filter/impute in data pipelines
- **JSON best practice:** Explicit absence of value

**Alternatives Considered:**
- Empty string `""`: Ambiguous (missing vs. empty)
- String `"null"`: Confusing (string vs. null type)
- Omit field: Inconsistent schema

### 7.3 Why Single JSON File?

**Decision:** Output single `menu_data.json` file

**Rationale:**
- **Simplicity:** Easier to implement and use
- **Reasonable size:** ~50-100 dishes = small file
- **Ease of consumption:** Single file to load
- **Assignment scope:** No requirement for splitting

**Alternatives Considered:**
- Multiple files by category: Overkill for this size
- Database output: Not requested
- CSV format: Less structured, harder for nested data

### 7.4 Why Package Structure?

**Decision:** Use `src/menu_extractor/` package structure

**Rationale:**
- **Maintainability:** Clear separation of concerns
- **Testability:** Easy to unit test individual modules
- **Scalability:** Easy to add new features (e.g., new PDF formats)
- **Readability:** Clear module responsibilities
- **Professional:** Industry standard structure

**Structure:**
```
src/menu_extractor/
├── __init__.py       # Package exports
├── extractor.py      # Orchestration
├── parser.py         # PDF parsing
└── normalizer.py     # Data cleaning
```

### 7.5 Why Test Against Actual PDF?

**Decision:** Write tests against `espn_bet.pdf` (not mocks)

**Rationale:**
- **Simplicity:** No need to create mock data
- **Real-world validation:** Catches actual PDF quirks
- **Evaluation criteria:** Assignment requires testing against actual PDF
- **Confidence:** Tests prove it works on the target data

**Trade-offs:**
- Tests depend on external file (acceptable for this scope)
- Slower than unit tests with mocks (negligible for 2-page PDF)

---

## 8. Edge Cases & Assumptions

### 8.1 Edge Cases to Handle

1. **Missing Prices**
   - Example: "SIGNATURE SAUCES" section
   - Solution: Set `price: null`

2. **Price Placeholders**
   - Example: "$X" in drinks section
   - Solution: Keep as-is (`"$X"`)

3. **Multi-line Descriptions**
   - Example: Most dishes have 2-3 line descriptions
   - Solution: Merge lines until next dish/category

4. **Two-Column Layout**
   - Example: Entire PDF is two-column
   - Solution: pdfplumber handles naturally

5. **Special Characters**
   - Example: Quotes, dashes, ampersands in descriptions
   - Solution: Preserve as-is (JSON escaping)

6. **Empty Descriptions**
   - Example: Some dishes may have no description
   - Solution: Empty string `""`

7. **Duplicate Dish Names**
   - Example: Unlikely but possible
   - Solution: Keep both, rely on dish_id for uniqueness

8. **Section Headers Without Dishes**
   - Example: Decorative headers
   - Solution: Skip if no dishes follow

### 8.2 Assumptions

1. **PDF Format:**
   - Two-column layout (verified)
   - Text-based PDF (not scanned image)
   - Consistent formatting throughout

2. **Data Format:**
   - Category headers are all-caps without prices
   - Dish names are on same line as prices
   - Descriptions are lowercase/mixed case
   - Prices follow format: `$XX` or `$X`

3. **Output Requirements:**
   - Sequential dish_id starting from "001"
   - Single JSON file output
   - All dishes from all categories

4. **Scope:**
   - Single PDF file (espn_bet.pdf)
   - No need for batch processing
   - No need for database storage
   - No need for API endpoints

---

## 9. Known Limitations & Next Steps

### 9.1 Known Limitations

1. **Single PDF Format:**
   - Designed specifically for espn_bet.pdf layout
   - May not work for different menu formats
   - No support for scanned/image PDFs

2. **Heuristic-Based Parsing:**
   - Relies on pattern matching (all-caps = category, etc.)
   - May fail on unexpected formats
   - No machine learning for robustness

3. **No OCR Support:**
   - Requires text-based PDFs
   - Cannot handle scanned menus

4. **Limited Error Recovery:**
   - Malformed lines are skipped
   - No attempt to fix/infer missing data

### 9.2 Next Steps (Future Enhancements)

**If this were a production system:**

1. **Support Multiple PDF Formats:**
   - Add format detection
   - Implement format-specific parsers
   - Use strategy pattern for parser selection

2. **Add OCR Support:**
   - Integrate Tesseract or cloud OCR
   - Handle scanned PDFs
   - Image preprocessing

3. **Improve Robustness:**
   - Machine learning for dish detection
   - Fuzzy matching for categories
   - Confidence scores for extractions

4. **Add Validation:**
   - Schema validation (JSON Schema)
   - Data quality checks
   - Completeness metrics

5. **Performance Optimization:**
   - Parallel processing for multi-page PDFs
   - Caching for repeated extractions
   - Streaming for large files

6. **API & Integration:**
   - REST API for extraction service
   - Batch processing endpoint
   - Webhook notifications

7. **Enhanced Output:**
   - Multiple format support (CSV, XML, etc.)
   - Database integration
   - Structured logging for analytics

---

## 10. Dependencies & Requirements

### 10.1 Python Version
- **Required:** Python 3.12 or higher
- **Reason:** Modern type hints, dataclasses, pattern matching

### 10.2 Core Dependencies

```txt
# PDF Processing
pdfplumber==0.11.0

# Testing
pytest==8.1.1
pytest-cov==5.0.0

# Type Checking (optional, for development)
mypy==1.9.0
```

### 10.3 Development Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (Unix/Mac)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/ -v

# Run extraction
python -m src.menu_extractor.extractor
```

---

## 11. Success Criteria

### 11.1 Functional Requirements
- ✅ Extract all dishes from espn_bet.pdf
- ✅ Preserve category information
- ✅ Merge multi-line descriptions
- ✅ Handle missing prices (null)
- ✅ Handle price placeholders ($X)
- ✅ Assign sequential dish_id (001, 002, ...)
- ✅ Output single JSON file

### 11.2 Quality Requirements
- ✅ Code is readable and well-structured
- ✅ Modules have clear responsibilities
- ✅ Unit tests cover key functions
- ✅ Integration tests validate full pipeline
- ✅ Error handling for common failures
- ✅ Logging for debugging

### 11.3 Documentation Requirements
- ✅ README.md with setup and usage
- ✅ Design decisions documented
- ✅ AI usage reflection completed
- ✅ Code comments for complex logic

### 11.4 Evaluation Criteria Alignment

| Criteria | Weight | How We Address |
|----------|--------|----------------|
| Approach & reasoning | 35% | Modular architecture, clear separation of concerns, justified design decisions |
| Extraction correctness & coverage | 35% | pdfplumber for layout preservation, multi-line merging, comprehensive testing |
| Data modeling & normalization | 20% | Clean JSON schema, null for missing prices, whitespace normalization |
| Code quality | 10% | Readable code, small helper functions, type hints, docstrings |

---

## 12. Risk Assessment

### 12.1 Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| pdfplumber fails on PDF | Low | High | Tested in experiments; fallback to PyMuPDF |
| Multi-line merging incorrect | Medium | Medium | Comprehensive tests; manual validation |
| Category detection fails | Low | Medium | Pattern matching tested; logging for debug |
| Performance issues | Low | Low | 2-page PDF is small; not a concern |

### 12.2 Schedule Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Implementation takes longer | Medium | Low | Modular design allows partial delivery |
| Testing reveals issues | Medium | Medium | Buffer time in schedule; iterative fixes |
| Documentation incomplete | Low | Low | Template prepared; fill as we go |

---

## 13. Conclusion

This plan provides a comprehensive roadmap for implementing a robust, maintainable menu extraction system. The modular architecture ensures clear separation of concerns, making the code easy to test, debug, and extend.

**Key Strengths:**
- Evidence-based design decisions (experiments)
- Clear module responsibilities
- Comprehensive testing strategy
- Graceful error handling
- Professional code structure

**Next Action:** Begin Phase 1 (Project Setup)

---

**Document Version:** 1.0  
**Last Updated:** 2026-05-01  
**Author:** Software Engineering Agent (Claude Code)
