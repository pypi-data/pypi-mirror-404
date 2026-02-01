"""
Basic usage examples for CaDaR

This script demonstrates the main features of CaDaR for
bidirectional Darija transliteration.
"""

import cadar

def example_ara2bizi():
    """Convert Arabic script to Latin (Bizi) script"""
    print("=" * 50)
    print("Example 1: Arabic to Latin (ara2bizi)")
    print("=" * 50)

    phrases = [
        "سلام عليكم",
        "كيفاش داير؟",
        "انا بخير",
        "شنو كدير؟",
        "بزاف ديال الناس",
    ]

    for phrase in phrases:
        result = cadar.ara2bizi(phrase, darija="Ma")
        print(f"{phrase:20} → {result}")
    print()


def example_bizi2ara():
    """Convert Latin (Bizi) script to Arabic script"""
    print("=" * 50)
    print("Example 2: Latin to Arabic (bizi2ara)")
    print("=" * 50)

    phrases = [
        "salam 3likom",
        "kifash dayer?",
        "ana bkhir",
        "shno kdir?",
        "bzaf dial nas",
    ]

    for phrase in phrases:
        result = cadar.bizi2ara(phrase, darija="Ma")
        print(f"{phrase:20} → {result}")
    print()


def example_ara2ara():
    """Standardize Arabic text"""
    print("=" * 50)
    print("Example 3: Arabic Standardization (ara2ara)")
    print("=" * 50)

    phrases = [
        "أنَا مِنْ المَغْرِب",  # With diacritics
        "أنا من المغرب",       # Without diacritics
        "إنا من المغرب",       # Different Alef
    ]

    for phrase in phrases:
        result = cadar.ara2ara(phrase, darija="Ma")
        print(f"{phrase:20} → {result}")
    print()


def example_bizi2bizi():
    """Standardize Latin text"""
    print("=" * 50)
    print("Example 4: Latin Standardization (bizi2bizi)")
    print("=" * 50)

    phrases = [
        "salaaaam",           # Repeated vowels
        "hellooooo",          # Repeated consonants
        "ki fash dayer",      # Separated words
        "b   zaf",            # Extra spaces
    ]

    for phrase in phrases:
        result = cadar.bizi2bizi(phrase, darija="Ma")
        print(f"{phrase:20} → {result}")
    print()


def example_using_class():
    """Using the CaDaR class for multiple operations"""
    print("=" * 50)
    print("Example 5: Using CaDaR Class")
    print("=" * 50)

    # Create a processor
    processor = cadar.CaDaR(darija="Ma")
    print(f"Processor dialect: {processor.get_dialect()}\n")

    # Multiple operations with same processor
    text1 = "واخا غير شوية"
    text2 = "wakha ghir shwiya"

    print(f"Arabic input: {text1}")
    print(f"  → Latin: {processor.ara2bizi(text1)}")
    print()

    print(f"Latin input: {text2}")
    print(f"  → Arabic: {processor.bizi2ara(text2)}")
    print()


def example_round_trip():
    """Demonstrate round-trip conversion"""
    print("=" * 50)
    print("Example 6: Round-trip Conversion")
    print("=" * 50)

    original = "salam dyal sbah"
    print(f"Original (Latin):  {original}")

    arabic = cadar.bizi2ara(original, darija="Ma")
    print(f"To Arabic:         {arabic}")

    back_to_latin = cadar.ara2bizi(arabic, darija="Ma")
    print(f"Back to Latin:     {back_to_latin}")
    print()


def example_convenience_functions():
    """Using convenience functions"""
    print("=" * 50)
    print("Example 7: Convenience Functions")
    print("=" * 50)

    # transliterate() with auto-detection
    text1 = "سلام"
    result1 = cadar.transliterate(text1, target="latin", darija="Ma")
    print(f"transliterate('{text1}', target='latin') → {result1}")

    text2 = "salam"
    result2 = cadar.transliterate(text2, target="arabic", darija="Ma")
    print(f"transliterate('{text2}', target='arabic') → {result2}")
    print()

    # standardize() with auto-detection
    text3 = "salaaaam bzaaaf"
    result3 = cadar.standardize(text3, script="auto", darija="Ma")
    print(f"standardize('{text3}', script='auto') → {result3}")
    print()


def main():
    """Run all examples"""
    print("\n")
    print("╔" + "═" * 48 + "╗")
    print("║" + " " * 10 + "CaDaR Usage Examples" + " " * 18 + "║")
    print("╚" + "═" * 48 + "╝")
    print()

    example_ara2bizi()
    example_bizi2ara()
    example_ara2ara()
    example_bizi2bizi()
    example_using_class()
    example_round_trip()
    example_convenience_functions()

    print("=" * 50)
    print("All examples completed!")
    print("=" * 50)


if __name__ == "__main__":
    main()
