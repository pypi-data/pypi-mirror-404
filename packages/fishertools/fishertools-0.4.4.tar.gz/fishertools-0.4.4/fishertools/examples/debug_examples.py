"""Examples of using the debug module."""

from fishertools.debug import debug_step_by_step, set_breakpoint, trace


def example_debug_step_by_step():
    """Example: Step-by-step debugging."""
    print("=" * 50)
    print("Example 1: Step-by-Step Debugging")
    print("=" * 50)

    @debug_step_by_step
    def calculate_average(numbers):
        """Calculate average of numbers."""
        total = sum(numbers)
        count = len(numbers)
        average = total / count
        return average

    result = calculate_average([1, 2, 3, 4, 5])
    print(f"Final result: {result}\n")


def example_trace():
    """Example: Execution tracing."""
    print("=" * 50)
    print("Example 2: Execution Tracing")
    print("=" * 50)

    @trace
    def fibonacci(n):
        """Calculate fibonacci number."""
        if n <= 1:
            return n
        return fibonacci(n - 1) + fibonacci(n - 2)

    result = fibonacci(4)
    print(f"Final result: {result}\n")


def example_breakpoint():
    """Example: Using breakpoints."""
    print("=" * 50)
    print("Example 3: Breakpoints")
    print("=" * 50)

    x = 10
    y = 20

    print(f"x = {x}, y = {y}")
    set_breakpoint("Check values before calculation")

    z = x + y
    print(f"z = {z}")

    set_breakpoint("Check result")

    result = z * 2
    print(f"result = {result}\n")


def example_complex_debug():
    """Example: Complex function debugging."""
    print("=" * 50)
    print("Example 4: Complex Function Debugging")
    print("=" * 50)

    @debug_step_by_step
    def process_data(data):
        """Process a list of numbers."""
        filtered = [x for x in data if x > 0]
        squared = [x ** 2 for x in filtered]
        total = sum(squared)
        return total

    result = process_data([1, -2, 3, -4, 5])
    print(f"Final result: {result}\n")


if __name__ == "__main__":
    example_debug_step_by_step()
    example_trace()
    example_breakpoint()
    example_complex_debug()
