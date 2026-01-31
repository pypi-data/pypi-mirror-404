# fishlib 🐟

A Python library for parsing, standardizing, and comparing seafood product descriptions in foodservice.

**The Problem:** Seafood product descriptions are messy. The same product can be described a hundred different ways. Comparing prices across distributors, suppliers, or market data requires deep domain knowledge to know if two items are actually comparable.

**The Solution:** `fishlib` parses item descriptions into structured attributes, standardizes them to common codes, and enables apples-to-apples comparisons—so you don't need to be a fish expert to work with seafood data.

## Installation

```bash
pip install fishlib
```

## Quick Start

```python
import fishlib

# Parse any item description
item = fishlib.parse("SALMON FIL ATL SKON DTRM 6OZ IVP")

print(item)
# {
#     'species': 'Atlantic Salmon',
#     'form': 'FIL',
#     'skin': 'SKON',
#     'bone': 'BNLS',
#     'trim': 'D',
#     'size': '6OZ',
#     'pack': 'IVP',
#     'storage': 'FRZ'
# }

# Get a comparison key for matching
key = fishlib.comparison_key(item)
print(key)
# "SALMON|ATLANTIC|FIL|SKON|BNLS|D|6OZ"

# Check if two items are comparable
distributor_item = "SALMON PORTION ATL BNLS SKLS 6 OZ CENTER CUT"
circana_item = "Portico Salmon Fillet 6 oz Boneless / Skinless"

match = fishlib.match(distributor_item, circana_item)
print(match)
# {
#     'is_match': True,
#     'confidence': 0.85,
#     'differences': ['form: PORTION vs FIL'],
#     'recommendation': 'Comparable with caution - form differs'
# }
```

## Features

### Parse Item Descriptions
Turn messy text into structured data:

```python
fishlib.parse("SALMON SOCKEYE FIL WILD ALASKA SKON 8OZ IQF")
# Returns structured dict with all attributes
```

### Standardize Codes
Consistent codes across any data source:

| Attribute | Codes |
|-----------|-------|
| **Form** | FIL (Fillet), PRTN (Portion), LOIN, WHL (Whole), STEAK, etc. |
| **Skin** | SKON (Skin On), SKLS (Skinless), SKOFF (Skin Off) |
| **Bone** | BNLS (Boneless), BIN (Bone In), PBO (Pin Bone Out) |
| **Trim** | A, B, C, D, E (see Trim Guide) |
| **Pack** | IVP, IQF, CVP, BULK |
| **Storage** | FRZ (Frozen), FRSH (Fresh), RFRSH (Refreshed) |

### Species Support
Built-in knowledge for major seafood categories:

- **Salmon**: Atlantic, King/Chinook, Sockeye, Coho, Keta/Chum, Pink
- **Crab**: King, Snow, Dungeness, Blue, Stone, Jonah, Soft Shell
- **Lobster**: Maine, Canadian, Warm Water, Spiny
- **Shrimp**: White, Pink, Brown, Tiger, Rock
- **Groundfish**: Cod, Haddock, Pollock, Hake, Whiting
- **Flatfish**: Flounder, Sole, Halibut, Turbot
- **Shellfish**: Scallops, Clams, Oysters, Mussels

### Reference Data
Access industry knowledge:

```python
# Salmon trim levels
fishlib.reference.trim_levels('salmon')
# Returns definitions for Trim A-E with skin status and pricing tier

# Species price tiers
fishlib.reference.price_tier('salmon', 'king')
# Returns: {'tier': 'ultra-premium', 'typical_range': (14.00, 17.00)}

# Cut style definitions
fishlib.reference.cut_style('center_cut')
# Returns: {'description': 'Portions from center of fish only...', 'premium': True}
```

### Match & Compare
Find comparable items across data sources:

```python
# Simple match
fishlib.is_comparable(item1, item2)  # Returns True/False

# Detailed match with confidence score
fishlib.match(item1, item2)  # Returns match details

# Find best matches in a list
fishlib.find_matches(target_item, list_of_items, threshold=0.8)
```

## Trim Guide (Salmon)

| Trim | Description | Skin |
|------|-------------|------|
| **A** | Backbone off, bellybone off | ON |
| **B** | + Backfin off, collarbone off, belly fat/fins off | ON |
| **C** | + Pin bone out | ON |
| **D** | + Back trimmed, tailpiece off, belly membrane off, nape trimmed | ON |
| **E** | Everything in D + skin removed | OFF |

**Key insight:** Trim A-D are all skin ON. Only Trim E is skin OFF.
**Foodservice standard:** Trim D (skin on) and Trim E (skin off).

## Cut Styles (Portions)

| Style | Description | Value |
|-------|-------------|-------|
| **Center Cut** | From center of fish only, no tails/nape | Premium |
| **Bias** | Cut at angle for better presentation | Premium |
| **Block** | Straight cuts end-to-end, includes tails | Mid |
| **Random** | Mixed pieces, various shapes | Value |

## Why This Exists

In foodservice distribution, comparing prices requires knowing if products are truly comparable. A "6oz salmon fillet" from two different sources might be:

- Center-cut bias portion at $12/lb (premium)
- Block-cut with tail pieces at $8/lb (commodity)

Without the right attributes, price comparisons are meaningless. `fishlib` encodes the domain knowledge needed to make accurate comparisons—so you don't need 20 years of fish experience to work with seafood data.

## Contributing

Contributions welcome! Areas of interest:

- Additional species and regional variants
- International market terminology
- Packaging and processing codes
- Price reference data

## Author

**Karen Morton** - Seafood industry professional with 20+ years of experience in category management and procurement.

Built from years of experience managing seafood categories and the realization that this knowledge should be accessible to everyone, not trapped in experts' heads.

## License

MIT License - Use it, modify it, share it. Just make seafood data better for everyone.
