"""
Tests for Menu Extractor

Integration tests against the actual espn_bet.pdf file.
"""

import json
import pytest
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from menu_extractor.extractor import MenuExtractor


class TestMenuExtractor:
    """Test suite for menu extraction."""

    @pytest.fixture
    def extractor(self):
        """Create extractor instance."""
        return MenuExtractor("data/espn_bet.pdf", "output/test_menu_data.json")

    def test_extractor_initialization(self, extractor):
        """Test extractor initializes correctly."""
        assert extractor.pdf_path == "data/espn_bet.pdf"
        assert extractor.output_path == "output/test_menu_data.json"
        assert extractor.parser is not None
        assert extractor.normalizer is not None

    def test_extract_dishes(self, extractor):
        """Test dish extraction from espn_bet.pdf."""
        dishes = extractor.extract()

        # Verify we extracted dishes
        assert len(dishes) > 0, "Should extract at least one dish"

        # Reasonable dish count for a 2-page menu
        assert 20 < len(dishes) < 120, f"Expected 20-120 dishes, got {len(dishes)}"

    def test_dish_structure(self, extractor):
        """Test that dishes have correct structure."""
        dishes = extractor.extract()

        for dish in dishes:
            # Required fields
            assert "dish_name" in dish, "Dish must have dish_name"
            assert "category" in dish, "Dish must have category"
            assert "dish_id" in dish, "Dish must have dish_id"
            assert "price" in dish, "Dish must have price field"
            assert "description" in dish, "Dish must have description field"

            # Field types
            assert isinstance(dish["dish_name"], str), "dish_name must be string"
            assert isinstance(dish["dish_id"], str), "dish_id must be string"
            assert isinstance(dish["description"], str), "description must be string"

            # Price can be string or None
            assert dish["price"] is None or isinstance(dish["price"], str), \
                "price must be string or null"

    def test_dish_ids_sequential(self, extractor):
        """Test that dish IDs are sequential."""
        dishes = extractor.extract()

        for idx, dish in enumerate(dishes, 1):
            expected_id = f"{idx:03d}"
            assert dish["dish_id"] == expected_id, \
                f"Expected dish_id {expected_id}, got {dish['dish_id']}"

    def test_categories_exist(self, extractor):
        """Test that dishes are categorized."""
        dishes = extractor.extract()

        # Get unique categories
        categories = set(d["category"] for d in dishes if d["category"])

        # Should have multiple categories
        assert len(categories) > 0, "Should have at least one category"

        # Check for known categories from the menu
        category_names = [c.upper() if c else "" for c in categories]

        # At least some dishes should be categorized
        categorized_dishes = [d for d in dishes if d["category"]]
        assert len(categorized_dishes) > 0, "Some dishes should have categories"

    def test_prices_format(self, extractor):
        """Test price formatting."""
        dishes = extractor.extract()

        for dish in dishes:
            price = dish["price"]

            if price is not None:
                # Price should start with $
                assert price.startswith("$"), f"Price should start with $: {price}"
                # Price should contain digits
                assert any(c.isdigit() for c in price), f"Price should contain digits: {price}"

    def test_null_prices_handled(self, extractor):
        """Test that items without prices have null."""
        dishes = extractor.extract()

        # Some items might not have prices (e.g., sauces, sides)
        null_price_dishes = [d for d in dishes if d["price"] is None]

        # If there are null prices, verify they're properly null (not string "null")
        for dish in null_price_dishes:
            assert dish["price"] is None, "Null prices should be None, not string"

    def test_save_to_json(self, extractor):
        """Test JSON output generation."""
        dishes = extractor.extract()
        extractor.save_to_json(dishes)

        # Verify file was created
        output_path = Path(extractor.output_path)
        assert output_path.exists(), "Output JSON file should be created"

        # Verify JSON is valid
        with open(output_path, 'r', encoding='utf-8') as f:
            loaded_dishes = json.load(f)

        assert len(loaded_dishes) == len(dishes), "Loaded dishes should match extracted"

        # Clean up test file
        output_path.unlink()

    def test_full_pipeline(self, extractor):
        """Test complete extraction pipeline."""
        dishes = extractor.run()

        # Verify output
        assert len(dishes) > 0, "Should extract dishes"

        # Verify JSON file exists
        output_path = Path(extractor.output_path)
        assert output_path.exists(), "Output file should exist"

        # Verify JSON content
        with open(output_path, 'r', encoding='utf-8') as f:
            loaded_dishes = json.load(f)

        assert len(loaded_dishes) == len(dishes), "JSON should contain all dishes"

        # Clean up
        output_path.unlink()

    def test_dish_names_not_empty(self, extractor):
        """Test that dish names are not empty."""
        dishes = extractor.extract()

        for dish in dishes:
            assert dish["dish_name"], f"Dish name should not be empty: {dish}"
            assert len(dish["dish_name"]) > 0, "Dish name should have content"

    def test_extraction_matches_expected_output(self):
        """Test that extracted menu data matches expected output exactly."""
        # Run extraction
        extractor = MenuExtractor("data/espn_bet.pdf", "output/menu_data.json")
        extractor.run()

        # Load actual output
        actual_path = Path('output/menu_data.json')
        with open(actual_path, 'r', encoding='utf-8') as f:
            actual = json.load(f)

        # Load expected output
        expected_path = Path('output/expected_menu_data.json')
        with open(expected_path, 'r', encoding='utf-8') as f:
            expected = json.load(f)

        # Compare total count
        assert len(actual) == len(expected), \
            f"Dish count mismatch: got {len(actual)}, expected {len(expected)}"

        # Compare each dish
        for i, (actual_dish, expected_dish) in enumerate(zip(actual, expected)):
            assert actual_dish['category'] == expected_dish['category'], \
                f"Dish {i}: category mismatch - got '{actual_dish['category']}', expected '{expected_dish['category']}'"

            assert actual_dish['dish_name'] == expected_dish['dish_name'], \
                f"Dish {i}: dish_name mismatch - got '{actual_dish['dish_name']}', expected '{expected_dish['dish_name']}'"

            assert actual_dish['price'] == expected_dish['price'], \
                f"Dish {i} ({actual_dish['dish_name']}): price mismatch - got '{actual_dish['price']}', expected '{expected_dish['price']}'"

            assert actual_dish['description'] == expected_dish['description'], \
                f"Dish {i} ({actual_dish['dish_name']}): description mismatch - got '{actual_dish['description']}', expected '{expected_dish['description']}'"

            assert actual_dish['dish_id'] == expected_dish['dish_id'], \
                f"Dish {i} ({actual_dish['dish_name']}): dish_id mismatch - got '{actual_dish['dish_id']}', expected '{expected_dish['dish_id']}'"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
