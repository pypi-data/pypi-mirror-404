"""
Demo script for execution tracing.
Run with: python -m blackbox --trace examples/trace_demo.py
"""


def validate(items: list) -> bool:
    """Validate the input items."""
    if not items:
        return False
    return all(isinstance(item, int) for item in items)


def transform(items: list) -> list:
    """Transform items by doubling them."""
    result = []
    for item in items:
        result.append(item * 2)
    return result


def process(items: list) -> list:
    """Main processing function."""
    if not validate(items):
        return []

    return transform(items)


def main():
    """Run the processing demo."""
    data = [1, 2, 3, 4, 5]
    result = process(data)
    print(f"Processed: {data} -> {result}")


if __name__ == '__main__':
    main()
