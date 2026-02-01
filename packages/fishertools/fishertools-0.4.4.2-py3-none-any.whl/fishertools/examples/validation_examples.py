"""Examples of using the validation module."""

from fishertools.validation import (
    validate_types,
    validate_email,
    validate_url,
    validate_number,
    validate_string,
    validate_structure,
    ValidationError,
)


def example_validate_types():
    """Example: Type validation with decorator."""
    print("=" * 50)
    print("Example 1: Type Validation")
    print("=" * 50)

    @validate_types
    def create_user(name: str, age: int, email: str) -> dict:
        """Create a user with type checking."""
        return {"name": name, "age": age, "email": email}

    # Correct usage
    try:
        user = create_user("Alice", 25, "alice@example.com")
        print(f"✅ User created: {user}")
    except ValidationError as e:
        print(f"❌ Error: {e}")

    # Incorrect usage
    try:
        user = create_user("Bob", "thirty", "bob@example.com")
        print(f"✅ User created: {user}")
    except ValidationError as e:
        print(f"❌ Error: {e}")


def example_validate_email():
    """Example: Email validation."""
    print("\n" + "=" * 50)
    print("Example 2: Email Validation")
    print("=" * 50)

    emails = [
        "user@example.com",
        "invalid-email",
        "test.user@example.co.uk",
    ]

    for email in emails:
        try:
            validate_email(email)
            print(f"✅ {email} is valid")
        except ValidationError as e:
            print(f"❌ {email} is invalid: {e}")


def example_validate_number():
    """Example: Number validation."""
    print("\n" + "=" * 50)
    print("Example 3: Number Validation")
    print("=" * 50)

    numbers = [42, 0, 100, 150, -1]

    for num in numbers:
        try:
            validate_number(num, min_val=0, max_val=100)
            print(f"✅ {num} is in range [0, 100]")
        except ValidationError as e:
            print(f"❌ {num} is out of range: {e}")


def example_validate_structure():
    """Example: Structure validation."""
    print("\n" + "=" * 50)
    print("Example 4: Structure Validation")
    print("=" * 50)

    schema = {"name": str, "age": int, "active": bool}

    data_list = [
        {"name": "Alice", "age": 25, "active": True},
        {"name": "Bob", "age": "thirty", "active": True},
        {"name": "Charlie", "age": 35},
    ]

    for data in data_list:
        try:
            validate_structure(data, schema)
            print(f"✅ {data} is valid")
        except ValidationError as e:
            print(f"❌ {data} is invalid: {e}")


if __name__ == "__main__":
    example_validate_types()
    example_validate_email()
    example_validate_number()
    example_validate_structure()
