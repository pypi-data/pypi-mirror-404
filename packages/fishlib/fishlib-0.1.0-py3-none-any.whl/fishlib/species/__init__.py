"""
Species module for fishlib.

Provides access to species-specific information including:
- Species identification and aliases
- Price tiers and typical ranges
- Subspecies/varieties
- Harvest methods
- Category information
"""

import json
import os
from typing import Dict, Any, Optional, List

# Load species data
_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
_SPECIES_FILE = os.path.join(_DATA_DIR, 'species_aliases.json')

try:
    with open(_SPECIES_FILE, 'r') as f:
        SPECIES_DATA = json.load(f)
except FileNotFoundError:
    SPECIES_DATA = {}


def get_species_info(category: str, subspecies: str = None) -> Optional[Dict[str, Any]]:
    """
    Get detailed information about a species.
    
    Args:
        category: The main category (e.g., 'salmon', 'crab', 'shrimp')
        subspecies: Optional specific type (e.g., 'atlantic', 'king', 'sockeye')
        
    Returns:
        Dictionary with species information or None if not found
        
    Example:
        >>> info = get_species_info('salmon', 'atlantic')
        >>> print(info['price_tier'])
        'mid'
        >>> print(info['typical_price_range'])
        [8.00, 11.00]
    """
    category = category.lower()
    
    if category not in SPECIES_DATA:
        return None
    
    cat_data = SPECIES_DATA[category]
    
    if subspecies:
        subspecies = subspecies.lower()
        if subspecies in cat_data.get('species', {}):
            result = cat_data['species'][subspecies].copy()
            result['category'] = category
            result['subspecies'] = subspecies
            return result
    
    # Return category-level info
    return {
        'category': category,
        'name': category.title(),
        'species_count': len(cat_data.get('species', {})),
        'forms': cat_data.get('forms', []),
        'has_trim_levels': 'trim_levels' in cat_data,
        'has_count_sizes': 'count_sizes' in cat_data
    }


def list_species(category: str = None) -> List[str]:
    """
    List available species.
    
    Args:
        category: If provided, list subspecies within that category.
                  If None, list all main categories.
                  
    Returns:
        List of species/category names
        
    Example:
        >>> list_species()
        ['salmon', 'crab', 'lobster', 'shrimp', ...]
        
        >>> list_species('salmon')
        ['atlantic', 'king', 'sockeye', 'coho', 'keta', 'pink']
    """
    if category is None:
        return list(SPECIES_DATA.keys())
    
    category = category.lower()
    if category in SPECIES_DATA:
        return list(SPECIES_DATA[category].get('species', {}).keys())
    
    return []


def get_price_tier(category: str, subspecies: str = None) -> Optional[str]:
    """
    Get the price tier for a species.
    
    Args:
        category: Main category
        subspecies: Specific type
        
    Returns:
        Price tier string: 'ultra-premium', 'premium', 'mid', 'value', 'economy'
        
    Example:
        >>> get_price_tier('salmon', 'king')
        'ultra-premium'
        >>> get_price_tier('salmon', 'pink')
        'economy'
    """
    info = get_species_info(category, subspecies)
    if info:
        return info.get('price_tier')
    return None


def get_price_range(category: str, subspecies: str = None) -> Optional[tuple]:
    """
    Get typical price range for a species.
    
    Args:
        category: Main category
        subspecies: Specific type
        
    Returns:
        Tuple of (low, high) prices in $/lb, or None if not available
        
    Example:
        >>> get_price_range('salmon', 'king')
        (14.00, 18.00)
    """
    info = get_species_info(category, subspecies)
    if info and 'typical_price_range' in info:
        return tuple(info['typical_price_range'])
    return None


def get_aliases(category: str, subspecies: str) -> List[str]:
    """
    Get all known aliases for a species.
    
    Useful for parsing item descriptions.
    
    Args:
        category: Main category
        subspecies: Specific type
        
    Returns:
        List of alias strings
        
    Example:
        >>> get_aliases('salmon', 'king')
        ['KING', 'CHINOOK', 'SPRING', 'TYEE', 'BLACKMOUTH', ...]
    """
    info = get_species_info(category, subspecies)
    if info:
        return info.get('aliases', [])
    return []


def identify_species(text: str) -> Optional[Dict[str, str]]:
    """
    Identify species from text description.
    
    Args:
        text: Item description text
        
    Returns:
        Dict with 'category' and 'subspecies' if identified, None otherwise
        
    Example:
        >>> identify_species("SALMON SOCKEYE FIL WILD AK")
        {'category': 'salmon', 'subspecies': 'sockeye'}
    """
    text_upper = text.upper()
    
    for category, cat_data in SPECIES_DATA.items():
        # Check for subspecies first (more specific)
        for subspecies, spec_info in cat_data.get('species', {}).items():
            for alias in spec_info.get('aliases', []):
                if alias in text_upper:
                    return {'category': category, 'subspecies': subspecies}
        
        # Check for category match
        if category.upper() in text_upper:
            return {'category': category, 'subspecies': None}
    
    return None


def get_harvest_type(category: str, subspecies: str) -> Optional[str]:
    """
    Get typical harvest type for a species.
    
    Args:
        category: Main category
        subspecies: Specific type
        
    Returns:
        'wild', 'farm', 'both', or None
        
    Example:
        >>> get_harvest_type('salmon', 'atlantic')
        'farm'
        >>> get_harvest_type('salmon', 'sockeye')
        'wild'
    """
    info = get_species_info(category, subspecies)
    if info:
        return info.get('harvest')
    return None


def compare_species_value(spec1: tuple, spec2: tuple) -> int:
    """
    Compare relative value of two species.
    
    Args:
        spec1: (category, subspecies) tuple
        spec2: (category, subspecies) tuple
        
    Returns:
        -1 if spec1 < spec2 (lower value)
         0 if approximately equal
         1 if spec1 > spec2 (higher value)
         
    Example:
        >>> compare_species_value(('salmon', 'king'), ('salmon', 'pink'))
        1  # King is higher value than Pink
    """
    tier_order = ['economy', 'value', 'mid', 'premium', 'ultra-premium']
    
    tier1 = get_price_tier(*spec1)
    tier2 = get_price_tier(*spec2)
    
    if tier1 is None or tier2 is None:
        return 0
    
    idx1 = tier_order.index(tier1) if tier1 in tier_order else 2
    idx2 = tier_order.index(tier2) if tier2 in tier_order else 2
    
    if idx1 < idx2:
        return -1
    elif idx1 > idx2:
        return 1
    else:
        return 0


# Convenience exports for specific categories
def salmon_species() -> Dict[str, Any]:
    """Get all salmon species data."""
    return SPECIES_DATA.get('salmon', {}).get('species', {})


def crab_species() -> Dict[str, Any]:
    """Get all crab species data."""
    return SPECIES_DATA.get('crab', {}).get('species', {})


def lobster_species() -> Dict[str, Any]:
    """Get all lobster species data."""
    return SPECIES_DATA.get('lobster', {}).get('species', {})


def shrimp_species() -> Dict[str, Any]:
    """Get all shrimp species data."""
    return SPECIES_DATA.get('shrimp', {}).get('species', {})


def shrimp_count_sizes() -> Dict[str, Any]:
    """Get shrimp count size definitions."""
    return SPECIES_DATA.get('shrimp', {}).get('count_sizes', {})


def scallop_count_sizes() -> Dict[str, Any]:
    """Get scallop count size definitions."""
    return SPECIES_DATA.get('scallop', {}).get('count_sizes', {})
