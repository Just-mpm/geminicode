#!/usr/bin/env python3
"""
Comprehensive test runner for Gemini Code.
"""

import pytest
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))


def run_all_tests():
    """Run all tests with comprehensive reporting."""
    
    # Test configuration
    test_args = [
        'tests/',
        '-v',  # Verbose output
        '--tb=short',  # Short traceback format
        '--strict-markers',  # Strict marker usage
        '--cov=gemini_code',  # Coverage for gemini_code package
        '--cov-report=term-missing',  # Show missing lines
        '--cov-report=html:htmlcov',  # HTML coverage report
        '--cov-fail-under=70',  # Minimum 70% coverage
        '--durations=10',  # Show 10 slowest tests
    ]
    
    print("🧪 Running Gemini Code Test Suite")
    print("=" * 50)
    
    # Run pytest
    exit_code = pytest.main(test_args)
    
    if exit_code == 0:
        print("\n✅ All tests passed!")
        print("📊 Coverage report generated in htmlcov/")
    else:
        print(f"\n❌ Tests failed with exit code: {exit_code}")
    
    return exit_code


def run_specific_tests():
    """Run specific test categories."""
    
    test_categories = {
        'core': 'tests/test_nlp_enhanced.py tests/test_memory_system.py tests/test_conversation_manager.py',
        'health': 'tests/test_refactored_health_monitor.py',
        'all': 'tests/'
    }
    
    if len(sys.argv) > 1:
        category = sys.argv[1]
        if category in test_categories:
            test_path = test_categories[category]
            print(f"🧪 Running {category} tests: {test_path}")
            return pytest.main([test_path, '-v'])
        else:
            print(f"❌ Unknown test category: {category}")
            print(f"Available categories: {list(test_categories.keys())}")
            return 1
    
    return run_all_tests()


if __name__ == "__main__":
    exit_code = run_specific_tests()
    sys.exit(exit_code)
