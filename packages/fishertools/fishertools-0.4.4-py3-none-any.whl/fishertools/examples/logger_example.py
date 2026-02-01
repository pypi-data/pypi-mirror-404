"""
Example demonstrating the SimpleLogger class from fishertools.patterns.

This example shows how to use SimpleLogger to add logging to applications
without complex configuration. Demonstrates info, warning, and error logging
with automatic timestamps and log levels.

Run this file to see SimpleLogger in action.
"""

import os
import time
from fishertools.patterns import SimpleLogger


def main():
    """Demonstrate SimpleLogger functionality."""
    
    # Constants for log file names
    DEMO_LOG_FILE = "demo_app.log"
    INFO_DEMO_LOG_FILE = "info_demo.log"
    NESTED_LOG_FILE = "logs/2024/01/application.log"
    
    print("=" * 70)
    print("fishertools Patterns - SimpleLogger Demo")
    print("=" * 70)
    
    # Create a logger instance
    log_file = DEMO_LOG_FILE
    logger = SimpleLogger(log_file)
    
    # Clean up any existing log file from previous runs
    if os.path.exists(log_file):
        os.remove(log_file)
        print(f"\n✓ Cleaned up existing {log_file}")
    
    # Example 1: Basic logging
    print("\n" + "─" * 70)
    print("Example 1: Basic logging with different levels")
    print("─" * 70)
    
    print("\nLogging messages...")
    logger.info("Application started")
    logger.info("Configuration loaded successfully")
    logger.warning("Deprecated API endpoint used")
    logger.error("Failed to connect to database")
    
    print("✓ Messages logged to", log_file)
    
    # Example 2: Simulating application workflow
    print("\n" + "─" * 70)
    print("Example 2: Simulating application workflow")
    print("─" * 70)
    
    print("\nSimulating user registration workflow...")
    
    logger.info("User registration started")
    logger.info("Validating email: user@example.com")
    
    time.sleep(0.5)  # Simulate processing
    
    logger.info("Email validation passed")
    logger.info("Checking username availability")
    
    time.sleep(0.5)  # Simulate processing
    
    logger.info("Username 'john_doe' is available")
    logger.info("Creating user account")
    
    time.sleep(0.5)  # Simulate processing
    
    logger.info("User account created successfully")
    logger.info("Sending welcome email")
    logger.info("User registration completed")
    
    print("✓ Workflow logged successfully")
    
    # Example 3: Error handling and warnings
    print("\n" + "─" * 70)
    print("Example 3: Error handling and warnings")
    print("─" * 70)
    
    print("\nSimulating error scenarios...")
    
    logger.warning("Memory usage above 80%")
    logger.warning("Cache hit rate below threshold")
    logger.error("Connection timeout after 30 seconds")
    logger.error("Failed to save user preferences")
    logger.info("Attempting automatic recovery")
    logger.info("Recovery successful")
    
    print("✓ Error scenarios logged")
    
    # Example 4: Nested directory logging
    print("\n" + "─" * 70)
    print("Example 4: Logging to nested directories")
    print("─" * 70)
    
    nested_log_file = NESTED_LOG_FILE
    nested_logger = SimpleLogger(nested_log_file)
    
    print(f"\nCreating logger for nested path: {nested_log_file}")
    nested_logger.info("Nested logging initialized")
    nested_logger.info("This log is in a nested directory structure")
    
    print(f"✓ Nested directories created automatically")
    print(f"✓ Logging to {nested_log_file}")
    
    # Example 5: Display the log file contents
    print("\n" + "─" * 70)
    print("Example 5: Reading log file contents")
    print("─" * 70)
    
    print(f"\nContents of {log_file}:")
    print("─" * 70)
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            log_contents = f.read()
            print(log_contents)
    except FileNotFoundError:
        print(f"✗ Log file {log_file} not found")
    
    print("─" * 70)
    
    # Example 6: Demonstrating log levels
    print("\n" + "─" * 70)
    print("Example 6: Different log levels")
    print("─" * 70)
    
    info_logger = SimpleLogger(INFO_DEMO_LOG_FILE)
    
    print("\nLogging different severity levels...")
    info_logger.info("This is an informational message")
    info_logger.warning("This is a warning message")
    info_logger.error("This is an error message")
    
    print("✓ Different log levels demonstrated")
    
    # Display the info demo log
    print(f"\nContents of {INFO_DEMO_LOG_FILE}:")
    print("─" * 70)
    
    try:
        with open(INFO_DEMO_LOG_FILE, 'r', encoding='utf-8') as f:
            print(f.read())
    except FileNotFoundError:
        print("✗ Log file not found")
    
    print("─" * 70)
    
    # Cleanup
    print("\n" + "─" * 70)
    print("Cleanup")
    print("─" * 70)
    
    files_to_remove = [log_file, INFO_DEMO_LOG_FILE, nested_log_file]
    
    for file_to_remove in files_to_remove:
        if os.path.exists(file_to_remove):
            os.remove(file_to_remove)
            print(f"✓ Removed {file_to_remove}")
    
    # Remove empty directories
    dirs_to_remove = ["logs/2024/01", "logs/2024", "logs"]
    
    for dir_to_remove in dirs_to_remove:
        if os.path.exists(dir_to_remove):
            try:
                os.rmdir(dir_to_remove)
                print(f"✓ Removed directory {dir_to_remove}")
            except OSError:
                pass
    
    print("\n" + "=" * 70)
    print("SimpleLogger demo complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
