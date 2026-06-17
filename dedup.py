"""Find candidate duplicate objectives (the dedup pre-filter).

Rung 1 of the dedup ladder from plans/lesson-planning.md: a cheap, deterministic
pass that decides which objective pairs are even worth a semantic look. It does
NOT decide anything -- a human (or, later, an automated semantic pass) judges the
surfaced candidates and merges.

Two signals make a pair a candidate:

- text similarity (character k-gram Jaccard, or LCS) at or above `threshold`; or
- the two objectives share a coverage node (most likely to be dupes) and clear a
  lower `node_threshold`.

Candidate pairs are unioned into clusters so the app/CLI can present a whole
group of likely-equivalent objectives at once.
"""

import jaccard as jaccard_mod
import lcs as lcs_mod

THRESHOLD = 0.5        # global text-similarity bar for a candidate pair
NODE_THRESHOLD = 0.3   # lower bar when the pair already shares a coverage node


def _scorer(method, k):
    """Return a function (a, b) -> similarity in [0, 1] for the chosen method."""
    if method == "lcs":
        return lambda a, b: lcs_mod.similarity(a, b)["total"]
    shingles = jaccard_mod.shingles

    def jac(sa, sb):
        return len(sa & sb) / len(sa | sb) if (sa or sb) else 1.0

    cache = {}

    def score(a, b):
        # Cache shingle sets by object identity of the text to avoid recompute.
        sa = cache.get(id(a)) or cache.setdefault(id(a), shingles(a, k))
        sb = cache.get(id(b)) or cache.setdefault(id(b), shingles(b, k))
        return jac(sa, sb)

    return score


def candidate_pairs(objs, coverage,
                    threshold=THRESHOLD, node_threshold=NODE_THRESHOLD,
                    method="jaccard", k=4):
    """Return scored candidate pairs among objectives.

    objs: list of (uuid, text). coverage: uuid -> set of node_ids. Each result is
    (uuid_a, uuid_b, similarity, sorted_shared_nodes), sorted by similarity desc.
    """
    score = _scorer(method, k)
    pairs = []
    for i in range(len(objs)):
        ua, ta = objs[i]
        for j in range(i + 1, len(objs)):
            ub, tb = objs[j]
            shared = coverage.get(ua, set()) & coverage.get(ub, set())
            sim = score(ta, tb)
            if sim >= threshold or (shared and sim >= node_threshold):
                pairs.append((ua, ub, sim, sorted(shared)))
    pairs.sort(key=lambda p: p[2], reverse=True)
    return pairs


def cluster(pairs):
    """Union candidate pairs into clusters. Returns list of sets of uuids (size >= 2)."""
    parent = {}

    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a, b, *_ in pairs:
        parent[find(a)] = find(b)

    groups = {}
    for x in parent:
        groups.setdefault(find(x), set()).add(x)
    return [g for g in groups.values() if len(g) >= 2]


def clusters_with_pairs(objs, coverage, **kw):
    """Return (clusters, pair_index) for display.

    clusters: list of sets of uuids. pair_index: (uuid_a, uuid_b) frozenset ->
    (similarity, shared_nodes), so a view can annotate within-cluster pairs.
    """
    pairs = candidate_pairs(objs, coverage, **kw)
    index = {frozenset((a, b)): (sim, shared) for a, b, sim, shared in pairs}
    groups = cluster(pairs)

    def best_sim(g):
        return max((index[frozenset((a, b))][0]
                    for a in g for b in g
                    if a < b and frozenset((a, b)) in index), default=0)

    groups.sort(key=lambda g: (-len(g), -best_sim(g)))
    return groups, index
