# PDF Extraction Methods - Comparison Results

**Date:** 2026-04-30  
**PDF:** data/espn_bet.pdf (2 pages, two-column menu layout)

## Quick Comparison

| Method | Layout Preservation | Price Detection | Multi-line Handling | Speed | Complexity |
|--------|-------------------|-----------------|-------------------|-------|------------|
| **PyPDF2** | ❌ Poor | ✅ Good | ❌ Poor | ⚡ Fast | ⭐ Simple |
| **pdfplumber** | ✅ Excellent | ✅ Excellent | ✅ Good | 🐢 Slower | ⭐⭐ Moderate |
| **PyMuPDF** | ✅ Good | ⚠️ Separated | ⚠️ Needs work | ⚡⚡ Very Fast | ⭐⭐ Moderate |
| **pdfminer.six** | ✅ Good | ⚠️ Separated | ⚠️ Needs work | 🐢 Slower | ⭐⭐⭐ Complex |

## Detailed Analysis

### 1. PyPDF2
**Preview:**
```
JUMBO GERMAN PRETZEL $16
caramelized onion dip, queso blanco, house-made honey mustard
CHEESE WEDGES  $14
marinara sauce
```

**Pros:**
- Simple API
- Prices appear on same line as dish names
- Fast extraction

**Cons:**
- No layout/positioning data
- Cannot detect columns reliably
- Multi-line descriptions may be hard to associate
- No table detection

**Verdict:** ❌ Not suitable for two-column menu extraction

---

### 2. pdfplumber
**Preview:**
```
CHOPPED SALAD $14
romaine lettuce, roasted chicken, avocado, tomatoes, cabbage, bacon, scallions, corn,
tortilla chips, citrus vinaigrette
HOUSE SALAD $12
iceberg lettuce, diced tomatoes, cucumbers, fried onion strings, shredded cheese
```

**Pros:**
- Excellent layout preservation
- Prices on same line as dish names
- Detected 1 table automatically
- 522 words with positioning data
- Best text flow for two-column layout

**Cons:**
- Slower than PyMuPDF
- Slightly more complex API

**Verdict:** ✅ **RECOMMENDED** - Best balance of accuracy and usability

---

### 3. PyMuPDF (fitz)
**Preview:**
```
JUMBO GERMAN PRETZEL	
$16
caramelized onion dip, queso blanco, house-made honey mustard
CHEESE WEDGES	
$14
marinara sauce
```

**Pros:**
- Very fast (fastest of all)
- 58 text blocks with positioning
- Good for structured layouts
- Excellent positioning data

**Cons:**
- Prices separated from dish names (on different lines)
- Requires more post-processing to associate prices with dishes
- Tab characters between elements

**Verdict:** ⚠️ Good alternative if speed is critical, but needs more parsing logic

---

### 4. pdfminer.six
**Preview:**
```
CHOPPED SALAD 
romaine lettuce, roasted chicken, avocado, tomatoes, cabbage, bacon, scallions, corn, 
tortilla chips, citrus vinaigrette
$14
HOUSE SALAD 
iceberg lettuce, diced tomatoes, cucumbers, fried onion strings, shredded cheese
```

**Pros:**
- Very detailed positioning (97 text elements)
- Handles complex layouts well
- Good for advanced use cases

**Cons:**
- Prices separated from dish names
- Most complex API
- Slower processing
- Requires significant post-processing

**Verdict:** ⚠️ Overkill for this use case

---

## Recommendation

**Use pdfplumber** for this assignment because:

1. ✅ Prices appear on same line as dish names (easier parsing)
2. ✅ Excellent two-column layout handling
3. ✅ Table detection capability (found 1 table)
4. ✅ Word-level positioning available if needed
5. ✅ Good balance of simplicity and power
6. ✅ Multi-line descriptions flow naturally

## Next Steps

1. Delete unused experiment files (PyPDF2, PyMuPDF, pdfminer.six)
2. Build main extraction script using pdfplumber
3. Implement pattern matching for:
   - Section headers (LEADING OFF, BURGERS, etc.)
   - Dish names + prices
   - Multi-line descriptions
   - Handle missing prices gracefully

## Files Generated

- `experiments/pypdf2_output.json`
- `experiments/pdfplumber_output.json` ⭐
- `experiments/pymupdf_output.json`
- `experiments/pdfminer_output.json`
