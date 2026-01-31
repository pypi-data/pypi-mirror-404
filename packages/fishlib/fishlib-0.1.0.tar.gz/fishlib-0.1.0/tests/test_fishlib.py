"""
Tests for fishlib.

Run with: pytest tests/
"""

import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fishlib import parse, comparison_key, is_comparable, match
from fishlib import standardize_form, standardize_skin, standardize_bone, standardize_trim
from fishlib.species import get_species_info, get_price_tier, list_species
from fishlib.reference import TRIM_LEVELS, CUT_STYLES, is_trim_skin_on


class TestParser:
    """Tests for the parser module."""
    
    def test_parse_salmon_basic(self):
        """Test basic salmon parsing."""
        result = parse("SALMON FIL ATL SKON 6OZ")
        assert result['category'] == 'salmon'
        assert result['form'] == 'FIL'
        assert result['skin'] == 'SKON'
        assert result['size'] == '6OZ'
    
    def test_parse_salmon_with_trim(self):
        """Test salmon with trim level."""
        result = parse("SALMON FIL ATL SKON DTRM 8OZ IVP")
        assert result['category'] == 'salmon'
        assert result['trim'] == 'D'
        assert result['pack'] == 'IVP'
    
    def test_parse_atlantic_salmon(self):
        """Test Atlantic salmon subspecies detection."""
        result = parse("SALMON ATL FIL BNLS SKLS 6OZ")
        assert result['category'] == 'salmon'
        assert result['subspecies'] == 'atlantic'
        assert result['bone'] == 'BNLS'
        assert result['skin'] == 'SKLS'
    
    def test_parse_wild_salmon_species(self):
        """Test wild salmon species detection."""
        result = parse("SALMON SOCKEYE FIL WILD AK SKON 8OZ")
        assert result['subspecies'] == 'sockeye'
        assert result['harvest'] == 'WILD'
        assert result['origin'] == 'USA'  # AK = Alaska = USA
    
    def test_parse_king_salmon(self):
        """Test king salmon detection."""
        result = parse("SALMON KING CHINOOK FIL WILD 6OZ")
        assert result['subspecies'] == 'king'
    
    def test_parse_crab(self):
        """Test crab parsing."""
        result = parse("CRAB KING LEG RED ALASKA 9/12")
        assert result['category'] == 'crab'
        assert result['subspecies'] == 'king'
        assert result['form'] == 'LEG'
    
    def test_parse_shrimp_with_count(self):
        """Test shrimp with count size."""
        result = parse("SHRIMP WHITE P&D 16/20 IQF")
        assert result['category'] == 'shrimp'
        assert result['count'] == '16/20'
        assert result['pack'] == 'IQF'
    
    def test_parse_shrimp_u_count(self):
        """Test shrimp with U-count."""
        result = parse("SHRIMP TIGER U10 HEAD ON")
        assert result['count'] == 'U10'
    
    def test_parse_lobster(self):
        """Test lobster parsing."""
        result = parse("LOBSTER TAIL MAINE 8OZ")
        assert result['category'] == 'lobster'
        assert result['form'] == 'TAIL'
        assert result['subspecies'] == 'maine'
    
    def test_parse_cod(self):
        """Test cod parsing."""
        result = parse("COD ATL FIL BNLS SKLS 4OZ IVP FRZ")
        assert result['category'] == 'cod'
        assert result['subspecies'] == 'atlantic'
        assert result['storage'] == 'FRZ'
    
    def test_parse_size_range(self):
        """Test size range parsing."""
        result = parse("SALMON FIL 5-7OZ BNLS SKLS")
        assert result['size'] == '5-7OZ'
    
    def test_parse_pound_size(self):
        """Test pound-based size parsing."""
        result = parse("SALMON FIL 2-3LB SKON")
        assert result['size'] == '2-3LB'
    
    def test_parse_brand_detection(self):
        """Test brand detection."""
        result = parse("PORTICO SALMON FIL ATL 6OZ")
        assert result['brand'] == 'Portico'
    
    def test_parse_empty_string(self):
        """Test empty string handling."""
        result = parse("")
        assert 'error' in result


class TestStandardization:
    """Tests for standardization functions."""
    
    def test_standardize_form_fillet(self):
        """Test form standardization."""
        assert standardize_form("FILLET") == "FIL"
        assert standardize_form("FILET") == "FIL"
        assert standardize_form("FIL") == "FIL"
    
    def test_standardize_form_portion(self):
        """Test portion form."""
        assert standardize_form("PORTION") == "PRTN"
        assert standardize_form("PORT") == "PRTN"
    
    def test_standardize_skin(self):
        """Test skin standardization."""
        assert standardize_skin("SKIN ON") == "SKON"
        assert standardize_skin("SKINLESS") == "SKLS"
        assert standardize_skin("SKIN OFF") == "SKOFF"
    
    def test_standardize_bone(self):
        """Test bone standardization."""
        assert standardize_bone("BONELESS") == "BNLS"
        assert standardize_bone("BONE IN") == "BIN"
        assert standardize_bone("PIN BONE OUT") == "PBO"
    
    def test_standardize_trim(self):
        """Test trim standardization."""
        assert standardize_trim("TRIM D") == "D"
        assert standardize_trim("DTRM") == "D"
        assert standardize_trim("E-TRIM") == "E"
        assert standardize_trim("FULL TRIM") == "FTRIM"


class TestComparisonKey:
    """Tests for comparison key generation."""
    
    def test_comparison_key_basic(self):
        """Test basic comparison key."""
        key = comparison_key("SALMON FIL ATL SKON 6OZ")
        assert "SALMON" in key
        assert "ATLANTIC" in key
        assert "FIL" in key
        assert "SKON" in key
        assert "6OZ" in key
    
    def test_comparison_key_consistency(self):
        """Test that similar descriptions produce same key."""
        key1 = comparison_key("SALMON FIL ATL 6OZ SKON")
        key2 = comparison_key("SALMON FILLET ATLANTIC 6 OZ SKIN ON")
        # Should have same components even if order differs
        assert set(key1.split('|')) == set(key2.split('|'))


class TestMatching:
    """Tests for matching functions."""
    
    def test_is_comparable_same_item(self):
        """Test that identical items are comparable."""
        assert is_comparable("SALMON FIL ATL 6OZ", "SALMON FIL ATL 6OZ")
    
    def test_is_comparable_different_species(self):
        """Test that different species are not comparable."""
        assert not is_comparable("SALMON FIL 6OZ", "COD FIL 6OZ")
    
    def test_match_high_confidence(self):
        """Test high confidence match."""
        result = match("SALMON FIL ATL 6OZ SKON", "SALMON FILLET ATLANTIC 6OZ SKIN ON")
        assert result['is_comparable'] == True
        assert result['confidence'] >= 0.8
    
    def test_match_details(self):
        """Test match returns expected fields."""
        result = match("SALMON FIL ATL 6OZ", "SALMON FIL ATL 8OZ")
        assert 'is_comparable' in result
        assert 'confidence' in result
        assert 'matching_attributes' in result
        assert 'different_attributes' in result
        assert 'recommendation' in result


class TestSpecies:
    """Tests for species module."""
    
    def test_list_species_categories(self):
        """Test listing species categories."""
        categories = list_species()
        assert 'salmon' in categories
        assert 'crab' in categories
        assert 'lobster' in categories
        assert 'shrimp' in categories
    
    def test_list_salmon_subspecies(self):
        """Test listing salmon subspecies."""
        subspecies = list_species('salmon')
        assert 'atlantic' in subspecies
        assert 'king' in subspecies
        assert 'sockeye' in subspecies
    
    def test_get_species_info(self):
        """Test getting species info."""
        info = get_species_info('salmon', 'atlantic')
        assert info is not None
        assert 'price_tier' in info
        assert 'typical_price_range' in info
    
    def test_get_price_tier(self):
        """Test price tier retrieval."""
        assert get_price_tier('salmon', 'king') == 'ultra-premium'
        assert get_price_tier('salmon', 'pink') == 'economy'
        assert get_price_tier('salmon', 'atlantic') == 'mid'


class TestReference:
    """Tests for reference data."""
    
    def test_trim_levels_exist(self):
        """Test trim levels data exists."""
        assert 'A' in TRIM_LEVELS
        assert 'B' in TRIM_LEVELS
        assert 'C' in TRIM_LEVELS
        assert 'D' in TRIM_LEVELS
        assert 'E' in TRIM_LEVELS
    
    def test_trim_skin_status(self):
        """Test trim level skin status."""
        # A-D are skin on, E is skin off
        assert is_trim_skin_on('A') == True
        assert is_trim_skin_on('B') == True
        assert is_trim_skin_on('C') == True
        assert is_trim_skin_on('D') == True
        assert is_trim_skin_on('E') == False
    
    def test_cut_styles_exist(self):
        """Test cut styles data exists."""
        assert 'CENTER' in CUT_STYLES
        assert 'BIAS' in CUT_STYLES
        assert 'BLOCK' in CUT_STYLES
        assert 'RANDOM' in CUT_STYLES
    
    def test_cut_style_premium_status(self):
        """Test cut style premium indicators."""
        assert CUT_STYLES['CENTER']['premium'] == True
        assert CUT_STYLES['BIAS']['premium'] == True
        assert CUT_STYLES['BLOCK']['premium'] == False


class TestRealWorldExamples:
    """Tests using real-world item descriptions."""
    
    def test_distributor_salmon_description(self):
        """Test typical distributor salmon description."""
        result = parse("SALMON PRTN ATL BNLS SKLS 6 OZ CENTER CUT IVP FRZ")
        assert result['category'] == 'salmon'
        assert result['subspecies'] == 'atlantic'
        assert result['form'] == 'PRTN'
        assert result['bone'] == 'BNLS'
        assert result['skin'] == 'SKLS'
        assert result['size'] == '6OZ'
        assert result['cut_style'] == 'CENTER'
        assert result['pack'] == 'IVP'
        assert result['storage'] == 'FRZ'
    
    def test_circana_salmon_description(self):
        """Test typical Circana item description."""
        result = parse("Portico Finfish - Frozen / Refrigerated Salmon Fillet 6 oz Boneless / Skinless 1/10 lb")
        assert result['category'] == 'salmon'
        assert result['form'] == 'FIL'
        assert result['bone'] == 'BNLS'
        assert result['skin'] == 'SKLS'
        assert result['size'] == '6OZ'
        assert result['brand'] == 'Portico'
    
    def test_compare_distributor_to_circana(self):
        """Test comparing distributor and Circana descriptions."""
        distributor = "SALMON PRTN ATL BNLS SKLS 6OZ CENTER CUT"
        circana = "Portico Salmon Fillet 6 oz Boneless / Skinless"
        
        result = match(distributor, circana)
        # Should match on species, size, skin, bone
        # May differ on form (PRTN vs FIL) - this is a known Circana gap
        assert result['is_comparable'] == True or 'form' in result['different_attributes']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
