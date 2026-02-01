"""
Example demonstrating the JSONStorage class from fishertools.patterns.

This example shows how to use JSONStorage to persist and retrieve data
in JSON format without writing file handling code. Demonstrates saving,
loading, and checking file existence.

Run this file to see JSONStorage in action.
"""

import os
from fishertools.patterns import JSONStorage


def main():
    """Demonstrate JSONStorage functionality."""
    
    print("=" * 70)
    print("fishertools Patterns - JSONStorage Demo")
    print("=" * 70)
    
    # Create a storage instance
    storage_path = "demo_data.json"
    storage = JSONStorage(storage_path)
    
    # Clean up any existing file from previous runs
    if os.path.exists(storage_path):
        os.remove(storage_path)
        print(f"\n✓ Cleaned up existing {storage_path}")
    
    # Example 1: Save data
    print("\n" + "─" * 70)
    print("Example 1: Saving data")
    print("─" * 70)
    
    user_data = {
        "name": "Alice Johnson",
        "age": 28,
        "email": "alice@example.com",
        "skills": ["Python", "JavaScript", "SQL"],
        "is_active": True,
        "metadata": {
            "created": "2024-01-15",
            "last_login": "2024-01-26"
        }
    }
    
    print(f"\nSaving user data to {storage_path}:")
    print(f"  {user_data}")
    
    storage.save(user_data)
    print("✓ Data saved successfully!")
    
    # Example 2: Check if file exists
    print("\n" + "─" * 70)
    print("Example 2: Checking file existence")
    print("─" * 70)
    
    if storage.exists():
        print(f"✓ File {storage_path} exists")
    else:
        print(f"✗ File {storage_path} does not exist")
    
    # Example 3: Load data
    print("\n" + "─" * 70)
    print("Example 3: Loading data")
    print("─" * 70)
    
    loaded_data = storage.load()
    print(f"\nLoaded data from {storage_path}:")
    print(f"  Name: {loaded_data['name']}")
    print(f"  Age: {loaded_data['age']}")
    print(f"  Email: {loaded_data['email']}")
    print(f"  Skills: {', '.join(loaded_data['skills'])}")
    print(f"  Active: {loaded_data['is_active']}")
    print(f"  Created: {loaded_data['metadata']['created']}")
    
    # Example 4: Update data
    print("\n" + "─" * 70)
    print("Example 4: Updating data")
    print("─" * 70)
    
    loaded_data['age'] = 29
    loaded_data['skills'].append("Docker")
    loaded_data['metadata']['last_login'] = "2024-01-26"
    
    print(f"\nUpdating user data:")
    print(f"  Age: 28 → {loaded_data['age']}")
    print(f"  Skills: Added 'Docker'")
    print(f"  Last login: Updated to 2024-01-26")
    
    storage.save(loaded_data)
    print("✓ Updated data saved!")
    
    # Example 5: Working with nested directories
    print("\n" + "─" * 70)
    print("Example 5: Creating nested directories")
    print("─" * 70)
    
    nested_storage_path = "data/users/profiles/alice.json"
    nested_storage = JSONStorage(nested_storage_path)
    
    profile_data = {
        "username": "alice_dev",
        "bio": "Python developer and open source enthusiast",
        "followers": 150,
        "following": 75
    }
    
    print(f"\nSaving profile to nested path: {nested_storage_path}")
    nested_storage.save(profile_data)
    print("✓ Nested directories created automatically!")
    print(f"✓ Profile saved to {nested_storage_path}")
    
    # Verify the nested file was created
    if nested_storage.exists():
        print(f"✓ Verified: {nested_storage_path} exists")
    
    # Example 6: Round-trip verification
    print("\n" + "─" * 70)
    print("Example 6: Round-trip verification")
    print("─" * 70)
    
    original_data = {
        "items": [1, 2, 3, 4, 5],
        "config": {
            "debug": True,
            "timeout": 30,
            "retries": 3
        },
        "tags": ["important", "urgent", "review"]
    }
    
    roundtrip_storage = JSONStorage("roundtrip_test.json")
    
    print(f"\nOriginal data:")
    print(f"  {original_data}")
    
    roundtrip_storage.save(original_data)
    loaded_roundtrip = roundtrip_storage.load()
    
    print(f"\nLoaded data:")
    print(f"  {loaded_roundtrip}")
    
    if original_data == loaded_roundtrip:
        print("✓ Round-trip successful: Data matches perfectly!")
    else:
        print("✗ Round-trip failed: Data mismatch")
    
    # Cleanup
    print("\n" + "─" * 70)
    print("Cleanup")
    print("─" * 70)
    
    for file_to_remove in [storage_path, nested_storage_path, "roundtrip_test.json"]:
        if os.path.exists(file_to_remove):
            os.remove(file_to_remove)
            print(f"✓ Removed {file_to_remove}")
    
    # Remove empty directories
    for dir_to_remove in ["data/users/profiles", "data/users", "data"]:
        if os.path.exists(dir_to_remove):
            try:
                os.rmdir(dir_to_remove)
                print(f"✓ Removed directory {dir_to_remove}")
            except OSError:
                pass
    
    print("\n" + "=" * 70)
    print("JSONStorage demo complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
