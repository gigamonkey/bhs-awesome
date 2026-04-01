"""
Jaccard similarity on character k-grams.
"""

from collections import Counter


def shingles(s, k=4):
    """Return the set of character k-grams of s."""
    return set(s[i:i+k] for i in range(len(s) - k + 1))


def jaccard(a, b, k=4):
    """Jaccard similarity of two strings based on their character k-grams.

    Returns a value in [0, 1] where 1.0 means identical shingle sets."""
    sa = shingles(a, k)
    sb = shingles(b, k)
    return len(sa & sb) / len(sa | sb) if sa or sb else 1.0


def jaccard_weighted(a, b, k=4):
    """Weighted Jaccard similarity using shingle counts (multiset intersection/union).

    Like jaccard() but counts how many times each k-gram appears, so repeated
    shingles contribute proportionally. Uses sum(min) / sum(max) over counts."""
    ca = Counter(a[i:i+k] for i in range(len(a) - k + 1))
    cb = Counter(b[i:i+k] for i in range(len(b) - k + 1))
    intersection = sum((ca & cb).values())
    union = sum((ca | cb).values())
    return intersection / union if union else 1.0


def similarity(a, b, k=4):
    """Return a dict with the same shape as lcs.similarity for easy swapping."""
    score = jaccard(a, b, k)
    return {
        "jaccard": score,
        "total": score,
    }


def weighted_similarity(a, b, k=4):
    """Return a dict with the same shape as lcs.similarity for easy swapping."""
    score = jaccard_weighted(a, b, k)
    return {
        "jaccard": score,
        "total": score,
    }
