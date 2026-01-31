"""
Demo script that crashes in various ways.
Run with: python -m blackbox examples/crash_demo.py
"""


class Parser:
    """Simple parser that can fail."""

    def __init__(self, strict: bool = True):
        self.strict = strict
        self.mode = 'default'

    def parse_value(self, text: str) -> int:
        """Parse text to integer."""
        if self.strict:
            # No fallback in strict mode
            return int(text)
        return self._safe_parse(text)

    def _safe_parse(self, text: str) -> int:
        try:
            return int(text)
        except ValueError:
            return 0


class DataProcessor:
    """Processes request data."""

    def __init__(self):
        self.parser = Parser(strict=True)
        self.results = []

    def process_request(self, data: dict) -> int:
        """Process incoming request data."""
        amount = data['amount']
        currency = data.get('currency', 'USD')

        # This will crash if amount is not numeric
        value = self.parser.parse_value(amount)

        self.results.append({
            'value': value,
            'currency': currency,
        })

        return value


def main():
    """Simulate processing a request with bad data."""
    processor = DataProcessor()

    # Good request
    processor.process_request({'amount': '100', 'currency': 'USD'})

    # Bad request - will crash
    processor.process_request({'amount': 'abc', 'currency': 'EUR'})


if __name__ == '__main__':
    main()
