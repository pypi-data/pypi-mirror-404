"""
Reference data module for fishlib.

Contains industry-standard definitions for:
- Trim levels (A-E)
- Cut styles (center cut, bias, block, etc.)
- Forms (fillet, portion, loin, etc.)
- Skin/bone codes
- Pack styles
- Price tiers

This information codifies fish industry knowledge so that anyone
can understand product attributes without being a fish expert.
"""

# =============================================================================
# TRIM LEVELS (Salmon specific, but applies to similar finfish)
# =============================================================================
TRIM_LEVELS = {
    'A': {
        'name': 'Trim A',
        'description': 'Backbone off, bellybone off',
        'skin': 'on',
        'removed': ['backbone', 'bellybone'],
        'remaining': ['backfin', 'collarbone', 'belly fat', 'belly fins', 'pin bones', 'skin', 'nape', 'tail piece'],
        'foodservice_common': False,
        'typical_use': 'Retail, specialty',
        'relative_price': 'mid-high'
    },
    'B': {
        'name': 'Trim B',
        'description': 'A + backfin off, collarbone off, belly fat off, belly fins off',
        'skin': 'on',
        'removed': ['backbone', 'bellybone', 'backfin', 'collarbone', 'belly fat', 'belly fins'],
        'remaining': ['pin bones', 'skin', 'nape', 'tail piece'],
        'foodservice_common': False,
        'typical_use': 'Retail',
        'relative_price': 'mid'
    },
    'C': {
        'name': 'Trim C',
        'description': 'B + pin bone out',
        'skin': 'on',
        'removed': ['backbone', 'bellybone', 'backfin', 'collarbone', 'belly fat', 'belly fins', 'pin bones'],
        'remaining': ['skin', 'nape', 'tail piece'],
        'foodservice_common': False,
        'typical_use': 'Retail, some foodservice',
        'relative_price': 'mid'
    },
    'D': {
        'name': 'Trim D',
        'description': 'C + back trimmed, tailpiece off, belly membrane off, nape trimmed. FOODSERVICE STANDARD.',
        'skin': 'on',
        'removed': ['backbone', 'bellybone', 'backfin', 'collarbone', 'belly fat', 'belly fins', 'pin bones', 'tail piece', 'belly membrane', 'back fat', 'nape excess'],
        'remaining': ['skin'],
        'foodservice_common': True,
        'typical_use': 'Foodservice - most common for skin-on products',
        'relative_price': 'mid-low'
    },
    'E': {
        'name': 'Trim E', 
        'description': 'D + skin off. Most fully trimmed. FOODSERVICE PREMIUM.',
        'skin': 'off',
        'removed': ['backbone', 'bellybone', 'backfin', 'collarbone', 'belly fat', 'belly fins', 'pin bones', 'tail piece', 'belly membrane', 'back fat', 'nape excess', 'skin'],
        'remaining': [],
        'foodservice_common': True,
        'typical_use': 'Foodservice - premium boneless skinless',
        'relative_price': 'high'
    },
    'FTRIM': {
        'name': 'Full Trim',
        'description': 'Fully trimmed - typically equivalent to Trim E',
        'skin': 'typically off',
        'removed': ['all trim components'],
        'remaining': [],
        'foodservice_common': True,
        'typical_use': 'Foodservice',
        'relative_price': 'high'
    }
}

# Key insight about trim levels
TRIM_KEY_INSIGHT = """
CRITICAL: Trim A through D are ALL SKIN ON. Only Trim E is SKIN OFF.

Foodservice primarily uses:
- Trim D (skin on, fully trimmed) 
- Trim E (skin off, fully trimmed)

Trim A, B, C are more common in retail.

When comparing prices, Trim D vs Trim E represents a significant 
price difference ($2+ per lb) due to skin removal labor.
"""


# =============================================================================
# CUT STYLES (for portions)
# =============================================================================
CUT_STYLES = {
    'CENTER': {
        'name': 'Center Cut',
        'description': 'Portions cut from the center of the fish only. No tail or nape pieces.',
        'characteristics': ['Uniform thickness', 'Consistent shape', 'Best plate presentation'],
        'excludes': ['tail pieces', 'nape pieces', 'collar area'],
        'premium': True,
        'labor_intensity': 'high',
        'typical_price_impact': '+15-25% vs block cut',
        'foodservice_use': 'Fine dining, consistent portion control'
    },
    'BIAS': {
        'name': 'Bias Cut',
        'description': 'Cut at an angle (diagonal) rather than straight across.',
        'characteristics': ['Appears larger on plate', 'Better presentation', 'More surface area'],
        'premium': True,
        'labor_intensity': 'high',
        'typical_price_impact': '+10-20% vs straight cut',
        'foodservice_use': 'Upscale casual, fine dining'
    },
    'BLOCK': {
        'name': 'Block Cut',
        'description': 'Straight cuts through the entire fillet, end to end.',
        'characteristics': ['Includes tail pieces', 'Variable thickness', 'Rectangular shape'],
        'includes': ['tail pieces', 'nape pieces', 'variable shapes'],
        'premium': False,
        'labor_intensity': 'low',
        'typical_price_impact': 'baseline',
        'foodservice_use': 'Casual dining, high volume'
    },
    'RANDOM': {
        'name': 'Random/Irregular',
        'description': 'Mixed pieces of various shapes and sizes.',
        'characteristics': ['Variable shapes', 'May include trim pieces', 'Inconsistent'],
        'premium': False,
        'labor_intensity': 'minimal',
        'typical_price_impact': '-20-30% vs block cut',
        'foodservice_use': 'Buffet, fish tacos, stir fry, soups'
    }
}

CUT_STYLE_KEY_INSIGHT = """
WHY LABOR MATTERS FOR PRICE:

More precision = More labor = Higher price

Center-cut bias portions cost more because:
1. Skilled cutting at angles
2. Only center pieces used (tails/nape go elsewhere as lower-value products)
3. Consistency requires inspection and sorting

When Circana shows two '6oz salmon portions' at different prices, 
the difference is often cut style - not overpricing.
"""


# =============================================================================
# FORMS
# =============================================================================
FORMS = {
    'FIL': {
        'name': 'Fillet',
        'description': 'Boneless piece cut from the side of the fish',
        'typical_sizes': 'Sold by weight range (2-3#, 3-4#, etc.)',
        'requires': ['trim level', 'skin status'],
        'common_species': ['salmon', 'cod', 'tilapia', 'catfish', 'mahi']
    },
    'PRTN': {
        'name': 'Portion',
        'description': 'Pre-cut piece to exact weight for portion control',
        'typical_sizes': '3oz, 4oz, 5oz, 6oz, 7oz, 8oz, 10oz',
        'requires': ['cut style', 'trim level', 'skin status'],
        'common_species': ['salmon', 'cod', 'mahi', 'tilapia'],
        'note': 'Circana often misclassifies portions as fillets - major PMI gap'
    },
    'LOIN': {
        'name': 'Loin',
        'description': 'Premium center cut from the thickest part of the fillet',
        'characteristics': ['Highest yield', 'Most uniform', 'Premium price'],
        'common_species': ['salmon', 'tuna', 'swordfish', 'mahi']
    },
    'WHL': {
        'name': 'Whole',
        'description': 'Whole fish, may be head on or head off',
        'variants': ['round (as caught)', 'gutted', 'scaled', 'H&G'],
        'common_species': ['branzino', 'trout', 'snapper', 'lobster', 'crab']
    },
    'STEAK': {
        'name': 'Steak',
        'description': 'Cross-section cut through the fish, includes bone',
        'characteristics': ['Bone-in', 'Round shape', 'Good for grilling'],
        'common_species': ['salmon', 'swordfish', 'halibut', 'tuna']
    },
    'H&G': {
        'name': 'Headed & Gutted',
        'description': 'Whole fish with head and viscera removed',
        'common_species': ['salmon', 'cod', 'snapper']
    },
    'TAIL': {
        'name': 'Tail',
        'description': 'Tail section only',
        'common_species': ['lobster', 'monkfish'],
        'note': 'For lobster, this is the primary edible portion sold'
    },
    'CLUSTER': {
        'name': 'Cluster',
        'description': 'Section of legs/claws still connected to body section',
        'common_species': ['crab (snow, king)']
    },
    'MEAT': {
        'name': 'Meat/Picked',
        'description': 'Extracted meat, shell removed',
        'grades': ['jumbo lump', 'lump', 'backfin', 'claw', 'special'],
        'common_species': ['crab', 'lobster']
    }
}


# =============================================================================
# SKIN CODES
# =============================================================================
SKIN_CODES = {
    'SKON': {
        'name': 'Skin On',
        'description': 'Skin intact on the product',
        'trim_implication': 'For salmon: Trim A, B, C, or D',
        'cooking_note': 'Skin helps hold shape during cooking, can be crisped'
    },
    'SKLS': {
        'name': 'Skinless',
        'description': 'Skin has been removed',
        'trim_implication': 'For salmon: Trim E',
        'cooking_note': 'Faster cooking, no skin to remove at service'
    },
    'SKOFF': {
        'name': 'Skin Off',
        'description': 'Same as skinless - skin has been removed',
        'trim_implication': 'For salmon: Trim E',
        'note': 'SKOFF and SKLS are equivalent'
    }
}


# =============================================================================
# BONE CODES
# =============================================================================
BONE_CODES = {
    'BNLS': {
        'name': 'Boneless',
        'description': 'All bones removed',
        'note': 'Standard for foodservice fillets and portions'
    },
    'BIN': {
        'name': 'Bone In',
        'description': 'Bones present (e.g., steaks, whole fish)',
        'common_uses': ['steaks', 'whole fish', 'bone-in chops']
    },
    'PBO': {
        'name': 'Pin Bone Out',
        'description': 'Pin bones specifically removed',
        'note': 'Pin bones are the small intramuscular bones in fillets',
        'common_species': ['salmon', 'trout', 'herring']
    }
}


# =============================================================================
# PACK STYLES
# =============================================================================
PACK_STYLES = {
    'IVP': {
        'name': 'Individually Vacuum Packed',
        'description': 'Each piece vacuum sealed separately',
        'benefits': ['Longer shelf life', 'No freezer burn', 'Easy portioning'],
        'typical_users': 'Foodservice, retail premium'
    },
    'IQF': {
        'name': 'Individually Quick Frozen',
        'description': 'Each piece frozen separately, not stuck together',
        'benefits': ['Easy to separate', 'Use only what you need', 'Maintains quality'],
        'typical_users': 'High volume foodservice'
    },
    'CVP': {
        'name': 'Controlled Vacuum Pack',
        'description': 'Vacuum packed with controlled atmosphere',
        'benefits': ['Extended fresh shelf life', 'No freezing needed'],
        'typical_users': 'Fresh seafood programs'
    },
    'BULK': {
        'name': 'Bulk Pack',
        'description': 'Multiple pieces packed together, may be layer packed',
        'note': 'Lower cost, but pieces may stick together when frozen',
        'typical_users': 'High volume, cost-sensitive'
    },
    'SHL': {
        'name': 'Shatter Pack',
        'description': 'Frozen block that can be broken apart',
        'common_species': ['shrimp', 'small fish'],
        'typical_users': 'High volume operations'
    }
}


# =============================================================================
# PRICE TIERS
# =============================================================================
PRICE_TIERS = {
    'ultra-premium': {
        'description': 'Highest price tier, specialty/luxury items',
        'examples': ['king salmon', 'bluefin tuna', 'king crab', 'stone crab', 'dover sole'],
        'typical_markup': '40-60% above mid-tier'
    },
    'premium': {
        'description': 'High quality, above-average pricing',
        'examples': ['sockeye salmon', 'halibut', 'sea bass', 'diver scallops', 'maine lobster'],
        'typical_markup': '20-40% above mid-tier'
    },
    'mid': {
        'description': 'Standard foodservice quality',
        'examples': ['atlantic salmon', 'cod', 'mahi', 'snow crab', 'white shrimp'],
        'typical_markup': 'baseline'
    },
    'value': {
        'description': 'Cost-effective options',
        'examples': ['keta salmon', 'pollock', 'swai', 'calico scallops', 'jonah crab'],
        'typical_markup': '15-30% below mid-tier'
    },
    'economy': {
        'description': 'Lowest cost tier',
        'examples': ['pink salmon', 'tilapia', 'imitation crab'],
        'typical_markup': '30-50% below mid-tier'
    }
}


# =============================================================================
# SPECIES DATA (loaded from JSON but key facts here)
# =============================================================================
import json
import os

_DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
_SPECIES_FILE = os.path.join(_DATA_DIR, 'species_aliases.json')

try:
    with open(_SPECIES_FILE, 'r') as f:
        SPECIES_DATA = json.load(f)
except FileNotFoundError:
    SPECIES_DATA = {}


def get_trim_info(level: str) -> dict:
    """Get information about a trim level."""
    return TRIM_LEVELS.get(level.upper(), {})


def get_cut_style_info(style: str) -> dict:
    """Get information about a cut style."""
    return CUT_STYLES.get(style.upper(), {})


def get_form_info(form: str) -> dict:
    """Get information about a form type."""
    return FORMS.get(form.upper(), {})


def is_trim_skin_on(level: str) -> bool:
    """Check if a trim level is skin-on."""
    info = TRIM_LEVELS.get(level.upper(), {})
    return info.get('skin', '').lower() == 'on'


def is_foodservice_trim(level: str) -> bool:
    """Check if a trim level is common in foodservice."""
    info = TRIM_LEVELS.get(level.upper(), {})
    return info.get('foodservice_common', False)


def explain_price_difference(attr1: dict, attr2: dict) -> str:
    """
    Explain why two products might have different prices based on attributes.
    
    Args:
        attr1: First product attributes
        attr2: Second product attributes
        
    Returns:
        Human-readable explanation of price difference factors
    """
    factors = []
    
    # Check trim
    t1 = attr1.get('trim')
    t2 = attr2.get('trim')
    if t1 and t2 and t1 != t2:
        factors.append(f"Trim level: {t1} vs {t2} - different processing levels")
    
    # Check cut style
    c1 = attr1.get('cut_style')
    c2 = attr2.get('cut_style')
    if c1 and c2 and c1 != c2:
        info1 = CUT_STYLES.get(c1, {})
        info2 = CUT_STYLES.get(c2, {})
        if info1.get('premium') != info2.get('premium'):
            factors.append(f"Cut style: {c1} vs {c2} - different labor/precision")
    
    # Check subspecies
    s1 = attr1.get('subspecies')
    s2 = attr2.get('subspecies')
    if s1 and s2 and s1 != s2:
        factors.append(f"Species/variety: {s1} vs {s2} - different market value")
    
    # Check harvest
    h1 = attr1.get('harvest')
    h2 = attr2.get('harvest')
    if h1 and h2 and h1 != h2:
        factors.append(f"Harvest: {h1} vs {h2} - wild typically premium over farmed")
    
    if factors:
        return "Price difference may be justified by:\n- " + "\n- ".join(factors)
    else:
        return "No obvious attribute differences to explain price gap"
