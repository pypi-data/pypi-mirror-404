"""
Demo script that hangs (for testing --timeout feature).

Run with: python -m blackbox --timeout 2 examples/hang_demo.py
"""

import time
import os


def do_some_io():
    """Do some I/O operations before hanging."""
    # Read an env var
    debug = os.getenv('DEBUG', 'false')

    # Open a file
    with open(__file__, 'r') as f:
        content = f.read()

    return len(content)


def infinite_loop():
    """This function will hang."""
    i = 0
    while True:
        i += 1
        # Busy loop - will be interrupted by timeout
        if i % 1000000 == 0:
            pass  # Just to have something to do


def main():
    print("Starting hang demo...")

    # Do some I/O first (will show in breadcrumbs)
    file_size = do_some_io()
    print(f"Read {file_size} bytes from file")

    print("Entering infinite loop...")
    infinite_loop()

    print("This will never be reached")


if __name__ == '__main__':
    main()
