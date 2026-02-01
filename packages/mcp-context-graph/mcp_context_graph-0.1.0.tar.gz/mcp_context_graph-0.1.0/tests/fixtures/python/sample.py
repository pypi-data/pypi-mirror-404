"""Sample Python file for testing tree-sitter parsing."""

from pathlib import Path


class Calculator:
    """A simple calculator class."""

    def __init__(self, initial_value: int = 0) -> None:
        self.value = initial_value

    def add(self, x: int) -> int:
        """Add x to the current value."""
        self.value += x
        return self.value

    def subtract(self, x: int) -> int:
        """Subtract x from the current value."""
        self.value -= x
        return self.value

    def multiply(self, x: int) -> int:
        """Multiply the current value by x."""
        self.value *= x
        return self.value


def calculate_sum(numbers: list[int]) -> int:
    """Calculate the sum of a list of numbers."""
    return sum(numbers)


def process_file(file_path: Path) -> str | None:
    """Process a file and return its contents."""
    if not file_path.exists():
        return None
    return file_path.read_text()


def main() -> None:
    """Main entry point."""
    calc = Calculator(10)
    calc.add(5)
    calc.multiply(2)

    numbers = [1, 2, 3, 4, 5]
    total = calculate_sum(numbers)
    print(f"Total: {total}")


if __name__ == "__main__":
    main()
