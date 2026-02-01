"""
Example demonstrating the explain() function from fishertools.learn.

This example shows how to use the explain() function to get structured
explanations for Python topics, including descriptions, usage guidance,
and code examples.

Run this file to see explanations for various Python topics.
"""

from fishertools.learn import explain


def main():
    """Demonstrate the explain() function with various topics."""
    
    print("=" * 70)
    print("fishertools Learning Tools - explain() Function Demo")
    print("=" * 70)
    
    # List of topics to demonstrate
    topics = ["list", "for", "lambda", "try", "with"]
    
    for topic in topics:
        try:
            print(f"\n{'─' * 70}")
            print(f"Topic: {topic.upper()}")
            print(f"{'─' * 70}")
            
            # Get the explanation
            explanation = explain(topic)
            
            # Display the explanation
            print(f"\n📖 Description:")
            print(f"   {explanation['description']}")
            
            print(f"\n💡 When to use:")
            print(f"   {explanation['when_to_use']}")
            
            print(f"\n💻 Example:")
            print("   " + "\n   ".join(explanation['example'].split("\n")))
            
        except ValueError as e:
            print(f"❌ Error: {e}")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
    
    # Demonstrate error handling with invalid topic
    print(f"\n{'─' * 70}")
    print("Demonstrating error handling with invalid topic:")
    print(f"{'─' * 70}")
    
    try:
        explain("invalid_topic_xyz")
    except ValueError as e:
        print(f"✓ Caught expected error:")
        print(f"  {e}")
    
    print("\n" + "=" * 70)
    print("Demo complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
