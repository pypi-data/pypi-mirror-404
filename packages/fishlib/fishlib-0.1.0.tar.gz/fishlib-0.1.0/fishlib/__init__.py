"""
fishlib - A Python library for parsing, standardizing, and comparing foodservice seafood products.

Created by Karen Morton
License: MIT

THE PROBLEM THIS SOLVES:
You need deep fish knowledge to know if a PMI comparison is accurate. A 6oz salmon 
portion might be $4/lb more than industry - but that's because it's a center-cut 
bias portion vs block-cut with tails. Without the right attributes, it looks like 
you're overpriced when you're comparing apples to oranges.

THE GOAL:
Capture attributes correctly so ANYONE can trust the data without being a fish expert.

Example usage:
    import fishlib
    
    # Parse an item description
    item = fishlib.parse("SALMON FIL ATL SKON DTRM 6OZ IVP")
    print(item)
    # {'species': 'Atlantic Salmon', 'form': 'FIL', 'skin': 'SKON', 
    #  'trim': 'D', 'size': '6OZ', 'pack': 'IVP'}
    
    # Get comparison key for matching
    key = fishlib.comparison_key(item)
    print(key)
    # 'SALMON|ATLANTIC|FIL|SKON|D|6OZ'
    
    # Check if two items are comparable
    result = fishlib.match("SALMON FIL ATL 6OZ", "Portico Salmon Fillet 6oz")
    print(result['is_comparable'])  # True
    print(result['confidence'])     # 0.92
"""

__version__ = "0.1.0"
__author__ = "Karen Morton"
__license__ = "MIT"

from .parser import parse, parse_description
from .standards import (
    standardize_form,
    standardize_skin,
    standardize_bone,
    standardize_trim,
    standardize_pack,
    standardize_storage,
    standardize_cut_style,
    standardize_harvest,
    standardize_origin,
    standardize_size,
    get_standard_code,
    list_codes
)
from .matcher import (
    comparison_key,
    match,
    is_comparable,
    find_matches,
    match_score
)
from . import species
from . import reference

__all__ = [
    # Parser functions
    'parse',
    'parse_description',
    
    # Standardization functions
    'standardize_form',
    'standardize_skin',
    'standardize_bone',
    'standardize_trim',
    'standardize_pack',
    'standardize_storage',
    'standardize_cut_style',
    'standardize_harvest',
    'standardize_origin',
    'standardize_size',
    'get_standard_code',
    'list_codes',
    
    # Matcher functions
    'comparison_key',
    'match',
    'is_comparable',
    'find_matches',
    'match_score',
    
    # Submodules
    'species',
    'reference',
]
