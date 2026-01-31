"""
Parser module for fishlib.

Parses seafood item descriptions into structured attribute dictionaries.
Handles messy, inconsistent text from various data sources.
"""

import re
import json
import os
from typing import Dict, Any, Optional, List, Tuple

# Load reference data
_DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

with open(os.path.join(_DATA_DIR, 'standard_codes.json'), 'r') as f:
    STANDARD_CODES = json.load(f)

with open(os.path.join(_DATA_DIR, 'species_aliases.json'), 'r') as f:
    SPECIES_DATA = json.load(f)


def parse(description: str) -> Dict[str, Any]:
    """
    Parse a seafood item description into structured attributes.
    
    This is the main entry point for parsing. It handles messy text from
    various sources (distributors, Circana, suppliers) and extracts standardized
    attributes.
    
    Args:
        description: The item description to parse
                    e.g., "SALMON FIL ATL SKON DTRM 6OZ IVP"
                    
    Returns:
        Dictionary with extracted attributes:
        {
            'raw': original description,
            'species': detected species name,
            'species_code': standardized species code,
            'category': species category (e.g., 'salmon', 'crab'),
            'subspecies': specific type (e.g., 'atlantic', 'king'),
            'form': form code (FIL, PRTN, LOIN, etc.),
            'skin': skin status (SKON, SKLS, SKOFF),
            'bone': bone status (BNLS, BIN, PBO),
            'trim': trim level (A, B, C, D, E, FTRIM),
            'size': size specification (6OZ, 5-7OZ, etc.),
            'pack': packaging (IVP, IQF, etc.),
            'storage': storage type (FRZ, FRSH, RFRSH),
            'harvest': harvest type (WILD, FARM),
            'origin': country of origin code,
            'cut_style': cut style (CENTER, BIAS, BLOCK),
            'brand': detected brand name,
            'count': count size for shrimp/scallops
        }
        
    Example:
        >>> item = parse("SALMON FIL ATL SKON DTRM 6OZ IVP")
        >>> print(item['species'])
        'Atlantic Salmon'
        >>> print(item['form'])
        'FIL'
        >>> print(item['trim'])
        'D'
    """
    if not description:
        return {'raw': '', 'error': 'Empty description'}
    
    result = {
        'raw': description,
        'species': None,
        'species_code': None,
        'category': None,
        'subspecies': None,
        'form': None,
        'skin': None,
        'bone': None,
        'trim': None,
        'size': None,
        'pack': None,
        'storage': None,
        'harvest': None,
        'origin': None,
        'cut_style': None,
        'brand': None,
        'count': None
    }
    
    # Normalize text
    text = description.upper().strip()
    
    # Extract species
    species_info = _extract_species(text)
    if species_info:
        result.update(species_info)
    
    # Extract form
    result['form'] = _extract_attribute(text, 'form')
    
    # Extract skin status
    result['skin'] = _extract_attribute(text, 'skin')
    
    # Extract bone status
    result['bone'] = _extract_attribute(text, 'bone')
    
    # Extract trim level
    result['trim'] = _extract_attribute(text, 'trim')
    
    # Extract size
    result['size'] = _extract_size(text)
    
    # Extract packaging
    result['pack'] = _extract_attribute(text, 'pack')
    
    # Extract storage
    result['storage'] = _extract_attribute(text, 'storage')
    
    # Extract harvest type
    result['harvest'] = _extract_attribute(text, 'harvest')
    
    # Extract origin
    result['origin'] = _extract_attribute(text, 'origin_country')
    
    # Extract cut style
    result['cut_style'] = _extract_attribute(text, 'cut_style')
    
    # Extract count (for shrimp, scallops)
    result['count'] = _extract_count(text)
    
    # Extract brand (common brands)
    result['brand'] = _extract_brand(text)
    
    return result


def parse_description(description: str) -> Dict[str, Any]:
    """
    Alias for parse() - for compatibility with different naming conventions.
    """
    return parse(description)


def _extract_species(text: str) -> Optional[Dict[str, Any]]:
    """
    Extract species information from text.
    
    Returns dict with species, species_code, category, subspecies.
    """
    text_upper = text.upper()
    
    # Check each category
    for category, cat_data in SPECIES_DATA.items():
        # Check if category name is in text
        if category.upper() in text_upper:
            # Try to find specific subspecies
            for subspec, spec_info in cat_data.get('species', {}).items():
                for alias in spec_info.get('aliases', []):
                    if alias in text_upper:
                        return {
                            'species': spec_info['name'],
                            'species_code': f"{category.upper()}|{subspec.upper()}",
                            'category': category,
                            'subspecies': subspec
                        }
            
            # No specific subspecies found, return category only
            return {
                'species': category.title(),
                'species_code': category.upper(),
                'category': category,
                'subspecies': None
            }
    
    # Check for species without category match (e.g., "ATL" for Atlantic Salmon)
    for category, cat_data in SPECIES_DATA.items():
        for subspec, spec_info in cat_data.get('species', {}).items():
            for alias in spec_info.get('aliases', []):
                if alias in text_upper and len(alias) >= 3:  # Avoid short false matches
                    return {
                        'species': spec_info['name'],
                        'species_code': f"{category.upper()}|{subspec.upper()}",
                        'category': category,
                        'subspecies': subspec
                    }
    
    return None


def _extract_attribute(text: str, category: str) -> Optional[str]:
    """
    Extract a standardized attribute from text.
    """
    if category not in STANDARD_CODES:
        return None
    
    text_upper = text.upper()
    
    # Sort by alias length descending to match longer aliases first
    # Also require word boundaries to avoid partial matches
    matches = []
    for code, info in STANDARD_CODES[category].items():
        for alias in info.get('aliases', []):
            # Check for word boundary match (surrounded by space, start, end, or punctuation)
            pattern = r'(?:^|[\s/\-_,])' + re.escape(alias) + r'(?:$|[\s/\-_,])'
            if re.search(pattern, text_upper) or text_upper == alias:
                matches.append((len(alias), code, alias))
    
    if matches:
        # Return the code with the longest matching alias
        matches.sort(reverse=True, key=lambda x: x[0])
        return matches[0][1]
    
    return None


def _extract_size(text: str) -> Optional[str]:
    """
    Extract size specification from text.
    
    Handles various formats:
    - "6 oz", "6OZ", "6 OZ"
    - "5-7 oz", "5-7OZ"
    - "3-4 lb", "3-4#"
    - "2-3#"
    """
    text_upper = text.upper()
    
    # Pattern for oz sizes
    oz_patterns = [
        r'(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s*(?:OZ|OUNCE)',  # 5-7 oz
        r'(\d+(?:\.\d+)?)\s*(?:OZ|OUNCE)',  # 6 oz
    ]
    
    for pattern in oz_patterns:
        match = re.search(pattern, text_upper)
        if match:
            if len(match.groups()) == 2:
                return f"{match.group(1)}-{match.group(2)}OZ"
            else:
                return f"{match.group(1)}OZ"
    
    # Pattern for lb sizes
    lb_patterns = [
        r'(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s*(?:LB|#|POUND)',  # 3-4 lb
        r'(\d+(?:\.\d+)?)\s*(?:LB|#|POUND)',  # 2 lb
    ]
    
    for pattern in lb_patterns:
        match = re.search(pattern, text_upper)
        if match:
            if len(match.groups()) == 2:
                return f"{match.group(1)}-{match.group(2)}LB"
            else:
                return f"{match.group(1)}LB"
    
    return None


def _extract_count(text: str) -> Optional[str]:
    """
    Extract count size (for shrimp, scallops).
    
    Handles:
    - "16/20", "21/25", "U10", "U/10"
    - "16-20 ct", "21-25 count"
    """
    text_upper = text.upper()
    
    # U-count pattern (under X)
    u_match = re.search(r'U[/-]?(\d+)', text_upper)
    if u_match:
        return f"U{u_match.group(1)}"
    
    # Range count pattern
    count_match = re.search(r'(\d+)\s*[/-]\s*(\d+)(?:\s*CT|\s*COUNT)?', text_upper)
    if count_match:
        return f"{count_match.group(1)}/{count_match.group(2)}"
    
    return None


def _extract_brand(text: str) -> Optional[str]:
    """
    Extract brand name from common foodservice brands.
    """
    COMMON_BRANDS = [
        'PORTICO', 'TRIDENT', 'HIGH LINER', 'HIGHLINER',
        'ICYBAY', 'SEAMAZZ', 'HARBOR BANKS', 'TRUE NORTH', 'SEAFARERS',
        'FISHERY PRODUCTS', 'FPI', 'NETUNO', 'PANAPESCE', 'PANAPESCA',
        'ACME', 'PHILLIPS', 'HANDY', 'TAMPA MAID', 'MRS FRIDAYS',
        'KING & PRINCE', 'CHICKEN OF THE SEA', 'BUMBLE BEE',
        'GORTONS', 'AQUASTAR', 'ICICLE', 'TRIDENT SEAFOODS',
        'OCEAN BEAUTY', 'PACIFIC SEAFOOD', 'CLEARWATER'
    ]
    
    text_upper = text.upper()
    
    for brand in COMMON_BRANDS:
        if brand in text_upper:
            return brand.title()
    
    return None


def parse_batch(descriptions: List[str]) -> List[Dict[str, Any]]:
    """
    Parse multiple descriptions at once.
    
    Args:
        descriptions: List of item descriptions
        
    Returns:
        List of parsed result dictionaries
    """
    return [parse(desc) for desc in descriptions]


def extract_key_attributes(description: str) -> Dict[str, str]:
    """
    Extract only the key attributes needed for matching.
    
    This is a simplified version of parse() that returns only
    the attributes typically used for comparison keys.
    
    Returns:
        Dict with: species, form, skin, bone, size, trim
    """
    result = parse(description)
    
    return {
        'species': result.get('subspecies') or result.get('category'),
        'form': result.get('form'),
        'skin': result.get('skin'),
        'bone': result.get('bone'),
        'size': result.get('size'),
        'trim': result.get('trim')
    }
