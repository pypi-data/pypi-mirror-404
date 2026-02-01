"""Examples of using the visualization module."""

from fishertools.visualization import visualize


def example_list_visualization():
    """Example: Visualizing a list."""
    print("=" * 50)
    print("Example 1: List Visualization")
    print("=" * 50)

    numbers = [10, 20, 30, 40, 50]
    print(visualize(numbers, title="Numbers List"))


def example_dict_visualization():
    """Example: Visualizing a dictionary."""
    print("\n" + "=" * 50)
    print("Example 2: Dictionary Visualization")
    print("=" * 50)

    user = {"name": "Alice", "age": 25, "email": "alice@example.com", "active": True}
    print(visualize(user, title="User Data"))


def example_nested_visualization():
    """Example: Visualizing nested structures."""
    print("\n" + "=" * 50)
    print("Example 3: Nested Structure Visualization")
    print("=" * 50)

    data = {
        "users": [
            {"name": "Alice", "age": 25},
            {"name": "Bob", "age": 30},
        ],
        "total": 2,
    }
    print(visualize(data, title="Users Database"))


def example_max_items():
    """Example: Limiting items shown."""
    print("\n" + "=" * 50)
    print("Example 4: Limiting Items")
    print("=" * 50)

    big_list = list(range(100))
    print(visualize(big_list, title="Large List (showing first 5)", max_items=5))


if __name__ == "__main__":
    example_list_visualization()
    example_dict_visualization()
    example_nested_visualization()
    example_max_items()
