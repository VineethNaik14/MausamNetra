"""Text cleaning shared by training and inference.
CRITICAL: train.py and predict.py must both call clean_text() —
never duplicate this logic, or you get train/inference skew.
"""

import re

URL_PATTERN = re.compile(r"https?://\S+|www\.\S+")
MENTION_PATTERN = re.compile(r"@\w+")
HASHTAG_SYMBOL_PATTERN = re.compile(r"#(\w+)")
PUNCT_PATTERN = re.compile(r"[^\w\s]")
MULTI_SPACE_PATTERN = re.compile(r"\s+")


def clean_text(text: str) -> str:
    """Normalize raw report text before vectorization.

    Steps (in order, each justified in the SIH writeup):
    1. Handle None/non-string input defensively
    2. Lowercase
    3. Strip URLs (no classification signal)
    4. Strip @mentions entirely (usernames are noise)
    5. Convert #hashtags to plain words (keep the signal, drop the symbol)
    6. Remove punctuation
    7. Collapse whitespace
    """
    if not isinstance(text, str) or text.strip() == "":
        return ""

    text = text.lower()
    text = URL_PATTERN.sub(" ", text)
    text = MENTION_PATTERN.sub(" ", text)
    text = HASHTAG_SYMBOL_PATTERN.sub(r"\1", text)
    text = PUNCT_PATTERN.sub(" ", text)
    text = MULTI_SPACE_PATTERN.sub(" ", text).strip()

    return text


if __name__ == "__main__":
    samples = [
        "Heavy rainfall has FLOODED the road near Hebbal!! http://example.com",
        "@someone check this out #flood #Bengaluru",
        None,
        "   ",
    ]
    for s in samples:
        print(repr(s), "->", repr(clean_text(s)))
