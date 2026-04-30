# PDF Extraction Method Comparison

This directory contains minimal working examples of different PDF extraction libraries to help choose the best approach for menu extraction.

## Files

- `test_pypdf2.py` - Basic text extraction (simple, no layout)
- `test_pdfplumber.py` - Layout-aware with column/table detection
- `test_pymupdf.py` - Fast extraction with positioning data
- `test_pdfminer.py` - Detailed text positioning for complex layouts

## Running the Tests

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run each test individually:
```bash
python experiments/test_pypdf2.py
python experiments/test_pdfplumber.py
python experiments/test_pymupdf.py
python experiments/test_pdfminer.py
```

Each script will:
- Extract text from `data/espn_bet.pdf`
- Show a preview in the console
- Save full output to `experiments/<library>_output.json`

## Comparison Criteria

- **Layout preservation** - Does it maintain column structure?
- **Positioning data** - Can we identify where text is located?
- **Speed** - How fast does it process?
- **Ease of use** - How complex is the API?
- **Multi-line handling** - Can we merge descriptions across lines?

## Next Steps

After reviewing outputs, choose the best library and delete the unused experiments.
