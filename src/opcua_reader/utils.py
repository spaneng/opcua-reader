import re

def to_camel_case(s: str) -> str:
    # Split on spaces, underscores, or dashes
    parts = re.split(r'[\s_-]+', s.strip())
    
    if not parts:
        return ""
    
    # First word lowercase, rest title-cased
    return parts[0].lower() + ''.join(word.capitalize() for word in parts[1:])