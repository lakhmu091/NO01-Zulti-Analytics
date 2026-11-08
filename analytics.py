from collections import Counter
from itertools import combinations

def number_universe(max_number):
    return list(range(1, max_number + 1))

def analyze(draws, max_number=45, draw_size=6):
    records = draws.to_dict("records")
    freq = Counter()
    pair_freq = Counter()
    triple_freq = Counter()
    for row in records:
        nums = sorted(set(int(x) for x in row["numbers"]))
        freq.update(nums)
        pair_freq.update(combinations(nums, 2))
        triple_freq.update(combinations(nums, 3))
    universe = number_universe(max_number)
    frequency = {n: freq.get(n, 0) for n in universe}
    last_seen = {}
    for idx, row in enumerate(records):
        for n in set(row["numbers"]):
            last_seen[int(n)] = idx
    total = len(records)
    gaps = {n: (total - 1 - last_seen[n]) if n in last_seen else total for n in universe}
    ranked_freq = sorted(universe, key=lambda n: (frequency[n], -n), reverse=True)
    ranked_cold = sorted(universe, key=lambda n: (frequency[n], n))
    ranked_gap = sorted(universe, key=lambda n: (gaps[n], n), reverse=True)
    return {
        "frequency": frequency,
        "hot": ranked_freq[:8],
        "cold": ranked_cold[:8],
        "overdue": ranked_gap[:8],
        "gaps": gaps,
        "pairs": [(k, v) for k, v in pair_freq.most_common()],
        "triples": [(k, v) for k, v in triple_freq.most_common()],
        "draw_count": total,
    }

def recommend_eight(stats, max_number=45):
    if stats["draw_count"] == 0:
        return []
    freq = stats["frequency"]
    gaps = stats["gaps"]
    max_freq = max(freq.values()) or 1
    max_gap = max(gaps.values()) or 1
    # Transparent heuristic score; deliberately not presented as probability.
    scored = []
    for n in range(1, max_number + 1):
        f_score = 100 * freq[n] / max_freq
        g_score = 100 * gaps[n] / max_gap
        score = round(0.70 * f_score + 0.30 * g_score, 2)
        scored.append({"Rank": 0, "Number": n, "Score": score,
                       "Historical frequency": freq[n], "Draws since seen": gaps[n]})
    scored.sort(key=lambda x: (-x["Score"], -x["Historical frequency"], x["Number"]))
    result = scored[:8]
    for i, item in enumerate(result, 1):
        item["Rank"] = i
    return result
