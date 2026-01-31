"""
Standardization functions for seafood product attributes.

Converts various text representations to standard codes.
"""

import json
import os
import re
from typing import Optional, Dict, Any

# Load standard codes from JSON
_DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
_CODES_FILE = os.path.join(_DATA_DIR, 'standard_codes.json')

with open(_CODES_FILE, 'r') as f:
    STANDARD_CODES = json.load(f)


def _find_match(text: str, category: str) -> Optional[str]:
    """
    Find a matching standard code for the given text in the specified category.
    
    Args:
        text: The text to match (will be uppercased)
        category: The category to search in (e.g., 'form', 'skin', 'bone')
        
    Returns:
        The standard code if found, None otherwise
    """
    if not text or category not in STANDARD_CODES:
        return None
    
    text_upper = text.upper().strip()
    
    # Check each code in the category
    for code, info in STANDARD_CODES[category].items():
        # Check if text matches the code itself
        if text_upper == code:
            return code
        
        # Check aliases
        for alias in info.get('aliases', []):
            if text_upper == alias or alias in text_upper:
                return code
    
    return None


def standardize_form(text: str) -> Optional[str]:
    """
    Standardize form/cut type.
    
    Examples:
        'FILLET' -> 'FIL'
        'PORTION' -> 'PRTN'
        'LOIN' -> 'LOIN'
        'WHOLE' -> 'WHL'
    
    Args:
        text: The form description to standardize
        
    Returns:
        Standard form code or None if not recognized
    """
    return _find_match(text, 'form')


def standardize_skin(text: str) -> Optional[str]:
    """
    Standardize skin status.
    
    Examples:
        'SKIN ON' -> 'SKON'
        'SKINLESS' -> 'SKLS'
        'SKIN OFF' -> 'SKOFF'
    
    Args:
        text: The skin status to standardize
        
    Returns:
        Standard skin code or None if not recognized
    """
    return _find_match(text, 'skin')


def standardize_bone(text: str) -> Optional[str]:
    """
    Standardize bone status.
    
    Examples:
        'BONELESS' -> 'BNLS'
        'BONE IN' -> 'BIN'
        'PIN BONE OUT' -> 'PBO'
    
    Args:
        text: The bone status to standardize
        
    Returns:
        Standard bone code or None if not recognized
    """
    return _find_match(text, 'bone')


def standardize_trim(text: str) -> Optional[str]:
    """
    Standardize trim level.
    
    Examples:
        'TRIM D' -> 'D'
        'DTRM' -> 'D'
        'FULL TRIM' -> 'FTRIM'
        'E-TRIM' -> 'E'
    
    Args:
        text: The trim level to standardize
        
    Returns:
        Standard trim code or None if not recognized
    """
    return _find_match(text, 'trim')


def standardize_pack(text: str) -> Optional[str]:
    """
    Standardize packaging type.
    
    Examples:
        'IVP' -> 'IVP'
        'IQF' -> 'IQF'
        'VACUUM PACK' -> 'IVP'
    
    Args:
        text: The packaging type to standardize
        
    Returns:
        Standard pack code or None if not recognized
    """
    return _find_match(text, 'pack')


def standardize_storage(text: str) -> Optional[str]:
    """
    Standardize storage type.
    
    Examples:
        'FROZEN' -> 'FRZ'
        'FRESH' -> 'FRSH'
        'PREVIOUSLY FROZEN' -> 'RFRSH'
    
    Args:
        text: The storage type to standardize
        
    Returns:
        Standard storage code or None if not recognized
    """
    return _find_match(text, 'storage')


def standardize_cut_style(text: str) -> Optional[str]:
    """
    Standardize cut style.
    
    Examples:
        'CENTER CUT' -> 'CENTER'
        'BIAS' -> 'BIAS'
        'BLOCK CUT' -> 'BLOCK'
    
    Args:
        text: The cut style to standardize
        
    Returns:
        Standard cut style code or None if not recognized
    """
    return _find_match(text, 'cut_style')


def standardize_harvest(text: str) -> Optional[str]:
    """
    Standardize harvest type.
    
    Examples:
        'WILD CAUGHT' -> 'WILD'
        'FARM RAISED' -> 'FARM'
    
    Args:
        text: The harvest type to standardize
        
    Returns:
        Standard harvest code or None if not recognized
    """
    return _find_match(text, 'harvest')


def standardize_origin(text: str) -> Optional[str]:
    """
    Standardize country of origin.
    
    Examples:
        'NORWAY' -> 'NOR'
        'CHILE' -> 'CHL'
        'ALASKA' -> 'USA'
    
    Args:
        text: The origin to standardize
        
    Returns:
        Standard origin code or None if not recognized
    """
    return _find_match(text, 'origin_country')


def standardize_size(text: str) -> Optional[str]:
    """
    Standardize size/weight specifications.
    
    Normalizes various size formats to a standard representation.
    
    Examples:
        '6 oz' -> '6OZ'
        '6OZ' -> '6OZ'
        '5-7 oz' -> '5-7OZ'
        '3-4 lb' -> '3-4LB'
    
    Args:
        text: The size specification to standardize
        
    Returns:
        Standardized size string or None if not recognized
    """
    if not text:
        return None
    
    text = text.upper().strip()
    
    # Remove common words
    text = re.sub(r'\b(SIZE|ABOUT|APPROX|APPROXIMATELY)\b', '', text)
    
    # Normalize spacing around hyphens
    text = re.sub(r'\s*-\s*', '-', text)
    
    # Pattern for oz sizes: "6 oz", "6oz", "5-7 oz", "5-7oz"
    oz_match = re.search(r'(\d+(?:-\d+)?)\s*(?:OZ|OUNCE)', text)
    if oz_match:
        return f"{oz_match.group(1)}OZ"
    
    # Pattern for lb sizes: "3-4 lb", "2 lb", "1.5lb"
    lb_match = re.search(r'(\d+(?:\.\d+)?(?:-\d+(?:\.\d+)?)?)\s*(?:LB|POUND|#)', text)
    if lb_match:
        return f"{lb_match.group(1)}LB"
    
    # Pattern for count sizes (shrimp, scallops): "16/20", "U10", "21-25"
    count_match = re.search(r'(U?\d+(?:[/-]\d+)?)\s*(?:CT|COUNT)?', text)
    if count_match:
        count = count_match.group(1).replace('-', '/')
        return count
    
    return None


def get_standard_code(attribute: str, value: str) -> Optional[str]:
    """
    Get the standard code for any attribute value.
    
    This is a convenience function that routes to the appropriate
    standardization function based on the attribute name.
    
    Args:
        attribute: The attribute type ('form', 'skin', 'bone', 'trim', etc.)
        value: The value to standardize
        
    Returns:
        Standard code or None if not recognized
    """
    standardizers = {
        'form': standardize_form,
        'skin': standardize_skin,
        'bone': standardize_bone,
        'trim': standardize_trim,
        'pack': standardize_pack,
        'storage': standardize_storage,
        'cut_style': standardize_cut_style,
        'harvest': standardize_harvest,
        'origin': standardize_origin,
        'size': standardize_size,
    }
    
    func = standardizers.get(attribute.lower())
    if func:
        return func(value)
    
    return None


def get_code_info(category: str, code: str) -> Optional[Dict[str, Any]]:
    """
    Get information about a standard code.
    
    Args:
        category: The category (e.g., 'form', 'skin')
        code: The standard code
        
    Returns:
        Dict with code info (name, aliases) or None if not found
    """
    if category in STANDARD_CODES and code in STANDARD_CODES[category]:
        return STANDARD_CODES[category][code]
    return None


def list_codes(category: str) -> Dict[str, str]:
    """
    List all standard codes in a category.
    
    Args:
        category: The category to list
        
    Returns:
        Dict mapping codes to their names
    """
    if category not in STANDARD_CODES:
        return {}
    
    return {code: info['name'] for code, info in STANDARD_CODES[category].items()}
