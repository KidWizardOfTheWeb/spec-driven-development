"""
Example application using Python 3.8+ features
"""

import re


def process_data(data: list) -> dict:
    """Process data using walrus operator (Python 3.8+)."""
    
    results = []
    
    # Walrus operator in while loop
    while (item := next((x for x in data if x > 10), None)) is not None:
        results.append(item)
        data.remove(item)
    
    # Walrus operator in if statement
    if (count := len(results)) > 0:
        print(f"Processed {count} items")
    
    return {"processed": results, "remaining": data}


def debug_values(x: int, y: int) -> None:
    """Use f-string = for debugging (Python 3.8+)."""
    
    # f-string with = automatically shows variable name and value
    print(f"{x=}, {y=}")
    
    result = x + y
    print(f"{result=}")
    
    # More complex expressions
    print(f"{x * y=}")
    print(f"{x / y if y != 0 else 'undefined'=}")


def validate_email(email: str) -> bool:
    """Validate email with walrus operator."""
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    # Use walrus operator in if statement
    if (match := re.match(pattern, email)):
        print(f"Valid email: {email}")
        return True
    else:
        print(f"Invalid email: {email}")
        return False


if __name__ == "__main__":
    # Test walrus operator
    data = [5, 15, 8, 20, 3, 25]
    result = process_data(data.copy())
    print(f"Results: {result}")
    
    # Test f-string debugging
    debug_values(10, 5)
    
    # Test email validation
    validate_email("test@example.com")
    validate_email("invalid-email")
