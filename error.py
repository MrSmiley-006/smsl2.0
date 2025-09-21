import sys

class SmSLError(Exception):
    def __init__(self, text, line):
        sys.exit(f"Error on line {line}: {text}")
