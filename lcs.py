"""
Longest Common Subsequence (LCS) utilities.
"""


def lcs(a, b):
    """Return the LCS of two strings."""
    return _lcs_reconstruct(_lcs_matrix(a, b), a, b)


def lcs_length(a, b):
    """Return the length of the LCS of two strings. Slightly cheaper than
    actually constructing the LCS."""
    return _lcs_matrix(a, b)[0][0]


def similarity(a, b):
    """Compute the similarity of two strings, returning a dict with four keys:
    a_to_b (percent of a that's in the LCS), b_to_a (percent of b that's in
    the LCS), total (the percent of the average length of a and b that's in the
    LCS), and edit (the edit distance using only inserts and deletes between a
    and b)."""
    shared = lcs_length(a, b)
    return {
        "a_to_b": _safe_divide(shared, len(a)),
        "b_to_a": _safe_divide(shared, len(b)),
        "total": _safe_divide(shared, (len(a) + len(b)) / 2),
        "edit": 2 * shared - (len(a) + len(b)),
    }


def _safe_divide(a, b):
    return 1 if b == 0 else a / b


################################################################################
# Internals


def _lcs_matrix(a, b):
    """Compute the matrix using dynamic programming."""
    matrix = [[0] * (len(a) + 1) for _ in range(len(b) + 1)]

    for i in range(len(a) - 1, -1, -1):
        for j in range(len(b) - 1, -1, -1):
            here, right, down, diag = _neighbors(matrix, i, j)
            matrix[j][i] = max(1 + diag if a[i] == b[j] else 0, right, down)

    return matrix


def _lcs_reconstruct(matrix, a, b):
    """Reconstruct the LCS from the matrix."""
    result = []
    i = 0
    j = 0

    while j < len(b) and i < len(a):
        here, right, down, diag = _neighbors(matrix, i, j)

        if right == down == diag == here - 1:
            result.append(a[i])
            i += 1
            j += 1
        elif down == here:
            j += 1
        elif right == here:
            i += 1

    return "".join(result)


def _neighbors(m, i, j):
    """Return (here, right, down, diag) values from the matrix."""
    return m[j][i], m[j][i + 1], m[j + 1][i], m[j + 1][i + 1]
