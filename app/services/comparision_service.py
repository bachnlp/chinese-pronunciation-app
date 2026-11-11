import difflib


def compare_texts(reference: str, recognized: str) -> dict:
    """Compare two strings and return a character-level diff summary."""
    ref_clean = (reference or "").replace(" ", "")
    rec_clean = (recognized or "").replace(" ", "")

    matcher = difflib.SequenceMatcher(None, ref_clean, rec_clean)
    similarity_ratio = matcher.ratio() * 100

    detailed_diff = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        ref_segment = ref_clean[i1:i2]
        rec_segment = rec_clean[j1:j2]

        if tag == 'equal':
            for char in ref_segment:
                detailed_diff.append({"char": char, "status": "correct"})
        elif tag == 'replace':
            for char in ref_segment:
                detailed_diff.append({"char": char, "status": "incorrect", "recognized_as": rec_segment})
        elif tag == 'delete':
            for char in ref_segment:
                detailed_diff.append({"char": char, "status": "missing"})
        elif tag == 'insert':
            for char in rec_segment:
                detailed_diff.append({"char": char, "status": "extra"})

    return {
        "similarity_score": round(similarity_ratio, 2),
        "is_perfect_match": (ref_clean == rec_clean),
        "detailed_diff": detailed_diff,
    }