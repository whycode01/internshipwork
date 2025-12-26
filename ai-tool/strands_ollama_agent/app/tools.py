from strands import tool


@tool
def letter_counter(word: str, letter: str) -> int:
    """Count how many times a letter appears in a word."""
    if not isinstance(word, str) or not isinstance(letter, str) or len(letter) != 1:
        raise ValueError("Provide a word and a single character letter.")
    count = word.lower().count(letter.lower())
    return count

@tool
def simple_calculator(expression: str) -> float:
    """Evaluate a simple mathematical expression."""
    try:
        # Basic safety check - only allow numbers, operators, and parentheses
        allowed_chars = set('0123456789+-*/().')
        if not all(c in allowed_chars or c.isspace() for c in expression):
            raise ValueError("Expression contains invalid characters")
        
        result = eval(expression)
        return float(result)
    except Exception as e:
        raise ValueError(f"Cannot evaluate expression: {e}")
