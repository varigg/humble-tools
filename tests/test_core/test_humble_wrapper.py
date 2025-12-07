"""Tests for humble_wrapper module, focusing on the complex parse_bundle_details() function."""

from humble_tools.core.humble_wrapper import parse_bundle_details


class TestParseBundleDetails:
    """Test suite for the complex parse_bundle_details() function."""

    def test_parse_basic_bundle_with_items(self):
        """Test parsing a bundle with basic metadata and items."""
        details_output = """Humble Book Bundle: Programming Books
Purchased       : 2023-01-15
Amount spent    : $15.00
Total size      : 125.5 MiB

  # | Sub-item                                                  | Format      | Total Size
----+-----------------------------------------------------------+-------------+------------
  1 | Python Crash Course                                       | EPUB, PDF   |   5.2 MiB
  2 | Clean Code                                                | EPUB, MOBI  |   3.8 MiB
"""
        result = parse_bundle_details(details_output)

        assert result["name"] == "Humble Book Bundle: Programming Books"
        assert result["purchased"] == "2023-01-15"
        assert result["amount"] == "$15.00"
        assert result["total_size"] == "125.5 MiB"
        assert len(result["items"]) == 2

        # Check first item
        assert result["items"][0]["number"] == 1
        assert result["items"][0]["name"] == "Python Crash Course"
        assert result["items"][0]["formats"] == ["EPUB", "PDF"]
        assert result["items"][0]["size"] == "5.2 MiB"

        # Check second item
        assert result["items"][1]["number"] == 2
        assert result["items"][1]["name"] == "Clean Code"
        assert result["items"][1]["formats"] == ["EPUB", "MOBI"]
        assert result["items"][1]["size"] == "3.8 MiB"

        # No keys in this bundle
        assert result["keys"] == []

    def test_parse_bundle_with_only_keys(self):
        """Test parsing a bundle that contains only game keys (no downloadable items)."""
        details_output = """Train Simulator Bundle
Purchased       : 2024-06-10
Amount spent    : $1.00
Total size      : 0 B

Keys in this bundle:

  # | Key Name                                                  | Redeemed
----+-----------------------------------------------------------+----------
  1 | Train Simulator Classic                                   |   Yes    
  2 | Train Simulator: Route Addon                              |   No     
  3 | Train Simulator: Loco Pack                                |   Yes    
  4 | Train Simulator: Special Edition                          |   No     
  5 | Train Simulator: DLC Pack 1                               |   No     
  6 | Train Simulator: DLC Pack 2                               |   Yes    

Visit https://www.humblebundle.com/home/keys to view all your keys
"""
        result = parse_bundle_details(details_output)

        assert result["name"] == "Train Simulator Bundle"
        assert result["purchased"] == "2024-06-10"
        assert result["amount"] == "$1.00"
        assert result["total_size"] == "0 B"

        # No downloadable items
        assert result["items"] == []

        # Check keys
        assert len(result["keys"]) == 6

        assert result["keys"][0]["number"] == 1
        assert result["keys"][0]["name"] == "Train Simulator Classic"
        assert result["keys"][0]["redeemed"] is True

        assert result["keys"][1]["number"] == 2
        assert result["keys"][1]["name"] == "Train Simulator: Route Addon"
        assert result["keys"][1]["redeemed"] is False

        assert result["keys"][5]["number"] == 6
        assert result["keys"][5]["name"] == "Train Simulator: DLC Pack 2"
        assert result["keys"][5]["redeemed"] is True

    def test_parse_bundle_with_items_and_keys(self):
        """Test parsing a bundle with both downloadable items and game keys."""
        details_output = """Humble Game Bundle: Mixed Content
Purchased       : 2024-03-20
Amount spent    : $25.00
Total size      : 15.3 GiB

  # | Sub-item                                                  | Format      | Total Size
----+-----------------------------------------------------------+-------------+------------
  1 | Game Soundtrack                                           | EPUB, PDF   |   125 MiB
  2 | Art Book                                                  | PDF         |   89 MiB

Keys in this bundle:

  # | Key Name                                                  | Redeemed
----+-----------------------------------------------------------+----------
  1 | Base Game (Steam)                                         |   Yes    
  2 | DLC Pack (Steam)                                          |   No     

Visit https://www.humblebundle.com/home/keys to view all your keys
"""
        result = parse_bundle_details(details_output)

        assert result["name"] == "Humble Game Bundle: Mixed Content"
        assert len(result["items"]) == 2
        assert len(result["keys"]) == 2

        # Check items
        assert result["items"][0]["name"] == "Game Soundtrack"
        assert result["items"][0]["formats"] == ["EPUB", "PDF"]

        # Check keys
        assert result["keys"][0]["name"] == "Base Game (Steam)"
        assert result["keys"][0]["redeemed"] is True
        assert result["keys"][1]["redeemed"] is False

    def test_parse_bundle_with_single_format(self):
        """Test parsing items that have only one format."""
        details_output = """Single Format Bundle
Purchased       : 2024-01-01
Amount spent    : $5.00
Total size      : 50 MiB

  # | Sub-item                                                  | Format      | Total Size
----+-----------------------------------------------------------+-------------+------------
  1 | PDF Only Book                                             | PDF         |   25 MiB
  2 | EPUB Only Book                                            | EPUB        |   25 MiB
"""
        result = parse_bundle_details(details_output)

        assert result["items"][0]["formats"] == ["PDF"]
        assert result["items"][1]["formats"] == ["EPUB"]

    def test_parse_bundle_with_multiple_formats(self):
        """Test parsing items with many format options."""
        details_output = """Multi-Format Bundle
Purchased       : 2024-01-01
Amount spent    : $10.00
Total size      : 100 MiB

  # | Sub-item                                                  | Format      | Total Size
----+-----------------------------------------------------------+-------------+------------
  1 | Complete Book                                             | EPUB, PDF, MOBI, AZW3 |   50 MiB
"""
        result = parse_bundle_details(details_output)

        assert result["items"][0]["formats"] == ["EPUB", "PDF", "MOBI", "AZW3"]

    def test_parse_bundle_with_long_item_names(self):
        """Test parsing items with very long names."""
        details_output = """Long Names Bundle
Purchased       : 2024-01-01
Amount spent    : $10.00
Total size      : 100 MiB

  # | Sub-item                                                  | Format      | Total Size
----+-----------------------------------------------------------+-------------+------------
  1 | This is a Very Long Book Title That Goes On and On and On | EPUB, PDF   |   50 MiB
  2 | Another Extremely Long Title With Many Words In It        | EPUB        |   25 MiB
"""
        result = parse_bundle_details(details_output)

        assert "Very Long Book Title" in result["items"][0]["name"]
        assert "Another Extremely Long Title" in result["items"][1]["name"]

    def test_parse_bundle_with_special_characters_in_names(self):
        """Test parsing items with special characters."""
        details_output = """Special Characters Bundle
Purchased       : 2024-01-01
Amount spent    : $10.00
Total size      : 100 MiB

  # | Sub-item                                                  | Format      | Total Size
----+-----------------------------------------------------------+-------------+------------
  1 | Book: The Sequel (Part 2) - Director's Cut               | EPUB, PDF   |   50 MiB
  2 | C++ & Python: A Developer's Guide [2024 Edition]         | PDF         |   25 MiB
"""
        result = parse_bundle_details(details_output)

        assert (
            result["items"][0]["name"] == "Book: The Sequel (Part 2) - Director's Cut"
        )
        assert (
            result["items"][1]["name"]
            == "C++ & Python: A Developer's Guide [2024 Edition]"
        )

    def test_parse_bundle_with_various_size_units(self):
        """Test parsing with different size units (B, KB, MB, GB)."""
        details_output = """Size Units Bundle
Purchased       : 2024-01-01
Amount spent    : $10.00
Total size      : 5.5 GiB

  # | Sub-item                                                  | Format      | Total Size
----+-----------------------------------------------------------+-------------+------------
  1 | Small File                                                | EPUB        |   512 KiB
  2 | Medium File                                               | PDF         |   25.5 MiB
  3 | Large File                                                | PDF         |   1.2 GiB
"""
        result = parse_bundle_details(details_output)

        assert result["items"][0]["size"] == "512 KiB"
        assert result["items"][1]["size"] == "25.5 MiB"
        assert result["items"][2]["size"] == "1.2 GiB"

    def test_parse_empty_bundle(self):
        """Test parsing a bundle with no items and no keys."""
        details_output = """Empty Bundle
Purchased       : 2024-01-01
Amount spent    : $0.00
Total size      : 0 B
"""
        result = parse_bundle_details(details_output)

        assert result["name"] == "Empty Bundle"
        assert result["items"] == []
        assert result["keys"] == []

    def test_parse_bundle_without_purchased_date(self):
        """Test parsing when purchased date is missing."""
        details_output = """No Date Bundle
Amount spent    : $10.00
Total size      : 100 MiB

  # | Sub-item                                                  | Format      | Total Size
----+-----------------------------------------------------------+-------------+------------
  1 | Some Book                                                 | EPUB        |   50 MiB
"""
        result = parse_bundle_details(details_output)

        assert result["purchased"] == ""
        assert result["name"] == "No Date Bundle"

    def test_parse_bundle_with_whitespace_variations(self):
        """Test parsing with various whitespace patterns."""
        details_output = """   Whitespace Bundle   
Purchased       :    2024-01-01   
Amount spent    :$10.00
Total size      : 100 MiB   

  # | Sub-item                                                  | Format      | Total Size
----+-----------------------------------------------------------+-------------+------------
  1 | Book Name                                                 | EPUB        |   50 MiB  
"""
        result = parse_bundle_details(details_output)

        # Should handle whitespace correctly
        assert "Whitespace Bundle" in result["name"]
        assert result["purchased"].strip() == "2024-01-01"
        assert result["items"][0]["name"] == "Book Name"

    def test_parse_bundle_with_decimal_item_numbers(self):
        """Test that item numbers are correctly parsed as integers."""
        details_output = """Number Test Bundle
Purchased       : 2024-01-01
Amount spent    : $10.00
Total size      : 100 MiB

  # | Sub-item                                                  | Format      | Total Size
----+-----------------------------------------------------------+-------------+------------
  1 | First Book                                                | EPUB        |   25 MiB
 10 | Tenth Book                                                | EPUB        |   25 MiB
 99 | Ninety-ninth Book                                         | EPUB        |   25 MiB
"""
        result = parse_bundle_details(details_output)

        assert result["items"][0]["number"] == 1
        assert result["items"][1]["number"] == 10
        assert result["items"][2]["number"] == 99

    def test_parse_preserves_key_order(self):
        """Test that items and keys maintain their order."""
        details_output = """Order Test Bundle
Purchased       : 2024-01-01
Amount spent    : $10.00
Total size      : 100 MiB

  # | Sub-item                                                  | Format      | Total Size
----+-----------------------------------------------------------+-------------+------------
  3 | Third                                                     | EPUB        |   25 MiB
  1 | First                                                     | EPUB        |   25 MiB
  2 | Second                                                    | EPUB        |   25 MiB

Keys in this bundle:

  # | Key Name                                                  | Redeemed
----+-----------------------------------------------------------+----------
  2 | Key Two                                                   |   No     
  1 | Key One                                                   |   Yes    
"""
        result = parse_bundle_details(details_output)

        # Should preserve the order from the output
        assert result["items"][0]["number"] == 3
        assert result["items"][1]["number"] == 1
        assert result["items"][2]["number"] == 2

        assert result["keys"][0]["number"] == 2
        assert result["keys"][1]["number"] == 1


class TestParseBundleDetailsEdgeCases:
    """Test edge cases and error conditions."""

    def test_parse_malformed_table_row(self):
        """Test that malformed rows are skipped gracefully."""
        details_output = """Malformed Bundle
Purchased       : 2024-01-01
Amount spent    : $10.00
Total size      : 100 MiB

  # | Sub-item                                                  | Format      | Total Size
----+-----------------------------------------------------------+-------------+------------
  1 | Good Book                                                 | EPUB        |   25 MiB
This is not a valid table row
  2 | Another Good Book                                         | PDF         |   25 MiB
"""
        result = parse_bundle_details(details_output)

        # Should parse the valid rows
        assert len(result["items"]) == 2
        assert result["items"][0]["name"] == "Good Book"
        assert result["items"][1]["name"] == "Another Good Book"

    def test_parse_with_missing_format_column(self):
        """Test handling of rows where format might be missing."""
        details_output = """Test Bundle
Purchased       : 2024-01-01
Amount spent    : $10.00
Total size      : 100 MiB

  # | Sub-item                                                  | Format      | Total Size
----+-----------------------------------------------------------+-------------+------------
  1 | Book With Format                                          | EPUB        |   25 MiB
"""
        result = parse_bundle_details(details_output)

        assert len(result["items"]) == 1
        assert result["items"][0]["formats"] == ["EPUB"]

    def test_parse_unicode_characters(self):
        """Test parsing with Unicode characters in names."""
        details_output = """Unicode Bundle
Purchased       : 2024-01-01
Amount spent    : €10.00
Total size      : 100 MiB

  # | Sub-item                                                  | Format      | Total Size
----+-----------------------------------------------------------+-------------+------------
  1 | Café Programming Guide ☕                                 | EPUB        |   25 MiB
  2 | 日本語 Japanese Language Book                              | PDF         |   25 MiB
"""
        result = parse_bundle_details(details_output)

        assert (
            "☕" in result["items"][0]["name"] or "Café" in result["items"][0]["name"]
        )
        assert (
            "日本語" in result["items"][1]["name"]
            or "Japanese" in result["items"][1]["name"]
        )

    def test_parse_empty_string(self):
        """Test parsing an empty string."""
        result = parse_bundle_details("")

        assert result["name"] == ""
        assert result["items"] == []
        assert result["keys"] == []

    def test_parse_only_whitespace(self):
        """Test parsing string with only whitespace."""
        result = parse_bundle_details("   \n\n   \n   ")

        assert result["items"] == []
        assert result["keys"] == []


class TestParseBundleDetailsRealWorldExamples:
    """Tests based on actual bundle output formats."""

    def test_parse_real_book_bundle(self):
        """Test with a realistic book bundle output."""
        details_output = """Humble Book Bundle: Web Development by Packt
Purchased       : 2023-11-15
Amount spent    : $18.00
Total size      : 256.8 MiB

  # | Sub-item                                                  | Format      | Total Size
----+-----------------------------------------------------------+-------------+------------
  1 | Learning React - Second Edition                           | EPUB, PDF   |   15.3 MiB
  2 | Full-Stack React Projects - Second Edition                | EPUB, PDF   |   24.7 MiB
  3 | React 18 Design Patterns and Best Practices               | EPUB, PDF   |   18.2 MiB
  4 | Node.js Design Patterns - Third Edition                   | EPUB, PDF   |   22.5 MiB
  5 | Building Enterprise JavaScript Applications               | EPUB, PDF   |   19.8 MiB
"""
        result = parse_bundle_details(details_output)

        assert "Web Development" in result["name"]
        assert len(result["items"]) == 5
        assert all(item["formats"] == ["EPUB", "PDF"] for item in result["items"])
        assert result["keys"] == []

    def test_parse_real_game_bundle_with_keys(self):
        """Test with a realistic game bundle that has only keys."""
        details_output = """Humble Monthly Bundle - December 2024
Purchased       : 2024-12-01
Amount spent    : $12.00
Total size      : 0 B

Keys in this bundle:

  # | Key Name                                                  | Redeemed
----+-----------------------------------------------------------+----------
  1 | Cyberpunk Adventure Game (Steam)                          |   Yes    
  2 | Indie Puzzle Collection (Steam)                           |   No     
  3 | RPG Starter Pack (Steam)                                  |   No     
  4 | Action Game Bundle DLC (Steam)                            |   Yes    

Visit https://www.humblebundle.com/home/keys to view all your keys
"""
        result = parse_bundle_details(details_output)

        assert "Monthly Bundle" in result["name"]
        assert result["items"] == []
        assert len(result["keys"]) == 4
        assert result["keys"][0]["redeemed"] is True
        assert result["keys"][1]["redeemed"] is False
