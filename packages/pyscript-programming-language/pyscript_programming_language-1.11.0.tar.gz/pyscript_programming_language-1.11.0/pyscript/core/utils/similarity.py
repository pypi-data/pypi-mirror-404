from itertools import pairwise
from re import compile as re_compile

replace = re_compile(r'\s+').sub

def get_similarity_ratio(string1, string2):
    bigram1 = set(s1 + s2 for s1, s2 in pairwise(replace('', string1).lower()))
    bigram2 = set(s1 + s2 for s1, s2 in pairwise(replace('', string2).lower()))
    max_bigrams_count = max(len(bigram1), len(bigram2))
    return len(bigram1 & bigram2) / max_bigrams_count if max_bigrams_count else 0.0

def get_closest(elements, target, cutoff=0.6):
    best_match = None
    best_score = 0.0

    for element in elements:
        score = get_similarity_ratio(target, element)
        if score >= cutoff and score > best_score:
            best_score = score
            best_match = element

    return best_match