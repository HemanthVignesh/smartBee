def contains_any(text: str, keywords: list) -> bool:
    text = text.lower()
    return any(keyword in text for keyword in keywords)
