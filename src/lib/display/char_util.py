def square_char(char: int) -> bool:
    """Checks if the character is square"""
    # CJK Unified Ideographs
    if 0x4E00 <= char <= 0x9FFF:
        return True
    # Hiragana
    if 0x3040 <= char <= 0x309F:
        return True
    # Katakana
    if 0x30A0 <= char <= 0x30FF:
        return True
    # Halfwidth and Fullwidth Forms (used for Katakana and punctuation)
    if 0xFF00 <= char <= 0xFFEF:
        return True
    # CJK Compatibility Ideographs
    if 0xF900 <= char <= 0xFAFF:
        return True
    # CJK Unified Ideographs Extension A
    if 0x3400 <= char <= 0x4DBF:
        return True
    return False

def ascii_char(char: int) -> bool:
    """Checks if the character is in ASCII range"""
    return char < 128
