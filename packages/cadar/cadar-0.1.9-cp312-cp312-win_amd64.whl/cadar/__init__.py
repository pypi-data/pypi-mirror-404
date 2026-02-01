"""
CaDaR: Canonicalization and Darija Representation

A high-performance bidirectional transliteration library for Darija (Moroccan Arabic)
with support for Arabic and Latin (Bizi) scripts.

Example usage:
    >>> import cadar
    >>>
    >>> # Convert Arabic to Latin
    >>> cadar.ara2bizi("سلام", darija="Ma")
    'slam'
    >>>
    >>> # Convert Latin to Arabic
    >>> cadar.bizi2ara("salam", darija="Ma")
    'سلام'
    >>>
    >>> # Standardize Arabic text
    >>> cadar.ara2ara("أنَا مِنْ المَغْرِب", darija="Ma")
    'انا من المغرب'
    >>>
    >>> # Standardize Latin text
    >>> cadar.bizi2bizi("salaaaam", darija="Ma")
    'salam'
    >>>
    >>> # Using the CaDaR class
    >>> processor = cadar.CaDaR(darija="Ma")
    >>> processor.ara2bizi("مرحبا")
    'mr7ba'
"""

__version__ = "0.1.9"
__author__ = "Ouail LAAMIRI"
__license__ = "MIT"

# Import from the Rust extension module
from ._cadar import (
    CaDaR,
    ara2bizi,
    bizi2ara,
    ara2ara,
    bizi2bizi,
)

__all__ = [
    "CaDaR",
    "ara2bizi",
    "bizi2ara",
    "ara2ara",
    "bizi2bizi",
]


# Convenience aliases for common use cases
def transliterate(text: str, target: str = "latin", darija: str = "Ma") -> str:
    """
    General-purpose transliteration function.

    Args:
        text: Input text to transliterate
        target: Target script - either "latin" or "arabic"
        darija: Dialect code (default: "Ma" for Moroccan Darija)

    Returns:
        Transliterated text

    Example:
        >>> transliterate("سلام", target="latin")
        'slam'
        >>> transliterate("salam", target="arabic")
        'سلام'
    """
    if target.lower() in ["latin", "bizi", "l"]:
        processor = CaDaR(darija=darija)
        return processor.ara2bizi(text)
    elif target.lower() in ["arabic", "ara", "a"]:
        processor = CaDaR(darija=darija)
        return processor.bizi2ara(text)
    else:
        raise ValueError(f"Unknown target script: {target}. Use 'latin' or 'arabic'")


def standardize(text: str, script: str = "auto", darija: str = "Ma") -> str:
    """
    Standardize text in the same script.

    Args:
        text: Input text to standardize
        script: Script type - "arabic", "latin", or "auto" (detect automatically)
        darija: Dialect code (default: "Ma" for Moroccan Darija)

    Returns:
        Standardized text

    Example:
        >>> standardize("أنَا مِنْ المَغْرِب", script="arabic")
        'انا من المغرب'
        >>> standardize("salaaaam", script="latin")
        'salam'
    """
    processor = CaDaR(darija=darija)

    if script.lower() == "auto":
        # Simple heuristic: if it contains Arabic characters, treat as Arabic
        has_arabic = any('\u0600' <= c <= '\u06FF' for c in text)
        script = "arabic" if has_arabic else "latin"

    if script.lower() in ["arabic", "ara", "a"]:
        return processor.ara2ara(text)
    elif script.lower() in ["latin", "bizi", "l"]:
        return processor.bizi2bizi(text)
    else:
        raise ValueError(f"Unknown script: {script}. Use 'arabic', 'latin', or 'auto'")
