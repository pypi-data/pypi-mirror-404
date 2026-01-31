"""
Matcher module for fishlib.

Provides functions for comparing seafood items and determining if they're comparable
for pricing analysis.
"""

from typing import Dict, Any, Optional, List, Tuple
from .parser import parse


def comparison_key(item: Any) -> str:
    """
    Generate a comparison key for matching items.
    
    The comparison key is a standardized string that can be used to 
    match similar products across different data sources.
    
    Args:
        item: Either a parsed item dict or a raw description string
        
    Returns:
        A pipe-delimited comparison key string
        e.g., "SALMON|ATLANTIC|FIL|SKON|BNLS|D|6OZ"
        
    Example:
        >>> key = comparison_key("SALMON FIL ATL SKON 6OZ")
        >>> print(key)
        'SALMON|ATLANTIC|FIL|SKON|6OZ'
    """
    # Parse if string provided
    if isinstance(item, str):
        item = parse(item)
    
    # Build key components
    components = []
    
    # Species/category (required)
    if item.get('category'):
        components.append(item['category'].upper())
        if item.get('subspecies'):
            components.append(item['subspecies'].upper())
    
    # Form
    if item.get('form'):
        components.append(item['form'])
    
    # Skin
    if item.get('skin'):
        components.append(item['skin'])
    
    # Bone
    if item.get('bone'):
        components.append(item['bone'])
    
    # Trim
    if item.get('trim'):
        components.append(item['trim'])
    
    # Size
    if item.get('size'):
        components.append(item['size'])
    
    # Count (for shrimp/scallops)
    if item.get('count'):
        components.append(item['count'])
    
    return '|'.join(components)


def match(item1: Any, item2: Any) -> Dict[str, Any]:
    """
    Compare two items and return detailed match information.
    
    Args:
        item1: First item (parsed dict or description string)
        item2: Second item (parsed dict or description string)
        
    Returns:
        Dictionary with match details:
        {
            'is_comparable': bool,
            'confidence': float (0-1),
            'match_score': float (0-1),
            'matching_attributes': list of matching attribute names,
            'different_attributes': list of different attribute names,
            'missing_attributes': list of attributes missing from one or both,
            'key1': comparison key for item 1,
            'key2': comparison key for item 2,
            'recommendation': string with matching recommendation
        }
        
    Example:
        >>> result = match("SALMON FIL ATL 6OZ", "Salmon Fillet Atlantic 6oz")
        >>> print(result['is_comparable'])
        True
        >>> print(result['confidence'])
        0.95
    """
    # Parse if needed
    if isinstance(item1, str):
        item1 = parse(item1)
    if isinstance(item2, str):
        item2 = parse(item2)
    
    # Get comparison keys
    key1 = comparison_key(item1)
    key2 = comparison_key(item2)
    
    # Compare attributes
    COMPARE_ATTRS = ['category', 'subspecies', 'form', 'skin', 'bone', 'trim', 'size', 'count', 'harvest', 'cut_style']
    
    matching = []
    different = []
    missing = []
    
    for attr in COMPARE_ATTRS:
        val1 = item1.get(attr)
        val2 = item2.get(attr)
        
        if val1 is None and val2 is None:
            continue
        elif val1 is None or val2 is None:
            missing.append(attr)
        elif str(val1).upper() == str(val2).upper():
            matching.append(attr)
        else:
            different.append(attr)
    
    # Calculate scores
    total_attrs = len(matching) + len(different)
    match_score = len(matching) / total_attrs if total_attrs > 0 else 0
    
    # Confidence score (penalize missing attributes less than differences)
    confidence = calculate_confidence(matching, different, missing)
    
    # Determine if comparable
    # Must match on species/category at minimum
    is_comparable = (
        'category' in matching and
        'subspecies' not in different and
        'form' not in different and
        match_score >= 0.5
    )
    
    # Generate recommendation
    recommendation = _generate_recommendation(matching, different, missing, is_comparable, confidence)
    
    return {
        'is_comparable': is_comparable,
        'confidence': round(confidence, 2),
        'match_score': round(match_score, 2),
        'matching_attributes': matching,
        'different_attributes': different,
        'missing_attributes': missing,
        'key1': key1,
        'key2': key2,
        'recommendation': recommendation
    }


def is_comparable(item1: Any, item2: Any, threshold: float = 0.7) -> bool:
    """
    Quick check if two items are comparable.
    
    Args:
        item1: First item (parsed dict or description string)
        item2: Second item (parsed dict or description string)
        threshold: Minimum confidence score to consider comparable (default 0.7)
        
    Returns:
        True if items are comparable, False otherwise
        
    Example:
        >>> is_comparable("SALMON FIL ATL 6OZ", "SALMON FIL ATL 6OZ")
        True
        >>> is_comparable("SALMON FIL", "COD FIL")
        False
    """
    result = match(item1, item2)
    return result['is_comparable'] and result['confidence'] >= threshold


def match_score(item1: Any, item2: Any) -> float:
    """
    Get just the match score between two items.
    
    Args:
        item1: First item
        item2: Second item
        
    Returns:
        Match score from 0 to 1
    """
    result = match(item1, item2)
    return result['match_score']


def find_matches(target: Any, candidates: List[Any], threshold: float = 0.7, top_n: int = 5) -> List[Dict[str, Any]]:
    """
    Find the best matching items from a list of candidates.
    
    Args:
        target: The item to match against
        candidates: List of candidate items to search
        threshold: Minimum confidence score (default 0.7)
        top_n: Maximum number of matches to return (default 5)
        
    Returns:
        List of match results, sorted by confidence descending
        Each result includes the candidate index and full match details
        
    Example:
        >>> candidates = ["SALMON FIL ATL 6OZ", "SALMON FIL ATL 8OZ", "COD FIL 6OZ"]
        >>> matches = find_matches("SALMON FILLET ATLANTIC 6 OZ", candidates)
        >>> print(matches[0]['confidence'])
        0.95
    """
    results = []
    
    for i, candidate in enumerate(candidates):
        match_result = match(target, candidate)
        match_result['candidate_index'] = i
        match_result['candidate'] = candidate if isinstance(candidate, str) else candidate.get('raw', str(candidate))
        
        if match_result['confidence'] >= threshold:
            results.append(match_result)
    
    # Sort by confidence descending
    results.sort(key=lambda x: x['confidence'], reverse=True)
    
    return results[:top_n]


def calculate_confidence(matching: List[str], different: List[str], missing: List[str]) -> float:
    """
    Calculate confidence score based on attribute matching.
    
    Weighting:
    - Matching attributes: positive
    - Different attributes: strong negative
    - Missing attributes: slight negative (data quality issue, not necessarily mismatch)
    
    Critical attributes (category, form) weighted higher.
    """
    # Attribute weights
    WEIGHTS = {
        'category': 3.0,      # Must match
        'subspecies': 2.0,    # Important for pricing
        'form': 2.5,          # Critical - fillet vs portion matters a lot
        'skin': 1.5,          # Important for salmon
        'bone': 1.0,          # Moderate importance
        'trim': 1.5,          # Important for salmon fillets
        'size': 2.0,          # Important for portions
        'count': 2.0,         # Important for shrimp/scallops
        'harvest': 1.5,       # Wild vs farm matters
        'cut_style': 1.5,     # Center cut vs block matters
    }
    
    score = 0
    max_score = 0
    
    # Add points for matching
    for attr in matching:
        weight = WEIGHTS.get(attr, 1.0)
        score += weight
        max_score += weight
    
    # Subtract points for different
    for attr in different:
        weight = WEIGHTS.get(attr, 1.0)
        score -= weight * 0.5  # Penalty
        max_score += weight
    
    # Slight penalty for missing (but not as bad as different)
    for attr in missing:
        weight = WEIGHTS.get(attr, 1.0)
        max_score += weight * 0.5  # Count at half weight for max
    
    if max_score == 0:
        return 0
    
    # Normalize to 0-1
    confidence = max(0, min(1, (score / max_score + 0.5)))
    
    return confidence


def _generate_recommendation(matching: List[str], different: List[str], missing: List[str], 
                             is_comparable: bool, confidence: float) -> str:
    """
    Generate a human-readable recommendation.
    """
    if not is_comparable:
        if 'category' in different:
            return "NOT COMPARABLE - Different species"
        elif 'form' in different:
            return "NOT COMPARABLE - Different form (e.g., fillet vs portion)"
        else:
            return "NOT COMPARABLE - Too many attribute differences"
    
    if confidence >= 0.9:
        return "EXCELLENT MATCH - High confidence comparison"
    elif confidence >= 0.8:
        return "GOOD MATCH - Reliable for PMI comparison"
    elif confidence >= 0.7:
        if missing:
            return f"FAIR MATCH - Missing data for: {', '.join(missing)}"
        else:
            return "FAIR MATCH - Some attribute differences"
    else:
        return f"WEAK MATCH - Differences in: {', '.join(different)}"


def explain_difference(item1: Any, item2: Any) -> str:
    """
    Generate a human-readable explanation of why two items differ.
    
    Useful for understanding why PMI comparisons might be misleading.
    
    Args:
        item1: First item
        item2: Second item
        
    Returns:
        String explanation of differences
    """
    result = match(item1, item2)
    
    lines = []
    lines.append(f"Comparison Key 1: {result['key1']}")
    lines.append(f"Comparison Key 2: {result['key2']}")
    lines.append("")
    
    if result['is_comparable']:
        lines.append(f"COMPARABLE (Confidence: {result['confidence']:.0%})")
    else:
        lines.append("NOT COMPARABLE")
    
    lines.append("")
    
    if result['matching_attributes']:
        lines.append(f"Matching: {', '.join(result['matching_attributes'])}")
    
    if result['different_attributes']:
        lines.append(f"Different: {', '.join(result['different_attributes'])}")
        
        # Parse both items for detailed comparison
        if isinstance(item1, str):
            item1 = parse(item1)
        if isinstance(item2, str):
            item2 = parse(item2)
        
        for attr in result['different_attributes']:
            val1 = item1.get(attr, 'N/A')
            val2 = item2.get(attr, 'N/A')
            lines.append(f"  - {attr}: '{val1}' vs '{val2}'")
    
    if result['missing_attributes']:
        lines.append(f"Missing data: {', '.join(result['missing_attributes'])}")
    
    lines.append("")
    lines.append(f"Recommendation: {result['recommendation']}")
    
    return '\n'.join(lines)
