import re
from typing import List, Tuple


def _tokenize(text: str) -> List[str]:
    # very simple tokenizer: words/numbers only
    return re.findall(r"[a-zA-Z0-9_]+", text.lower())


def keyword_retrieve(query: str, files: List[Tuple[str, str]], top_k: int = 3) -> List[Tuple[str, str]]:
    """
    A simple baseline retriever.
    files: list of (path, content)
    returns: top_k files ranked by token overlap score
    """
    q_tokens = set(_tokenize(query))
    scored = []
    for path, content in files:
        c_tokens = _tokenize(content)
        score = sum(1 for t in c_tokens if t in q_tokens)
        scored.append((score, path, content))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [(path, content) for score, path, content in scored[:top_k]]
