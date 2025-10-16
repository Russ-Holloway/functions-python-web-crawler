"""
Test Runner for Durable Functions Web Crawler
Phase 4 - Testing and Validation

Runs all test suites and generates reports
"""

import sys
import os
import unittest
from io import StringIO

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def run_unit_tests():
    """Run unit tests"""
    print("\n" + "=" * 60)
    print("RUNNING UNIT TESTS")
    print("=" * 60)
    
    # Discover and run unit tests
    loader = unittest.TestLoader()
    start_dir = os.path.dirname(__file__)
    suite = loader.discover(start_dir, pattern='test_unit.py')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


def run_integration_tests():
    """Run integration tests"""
    print("\n" + "=" * 60)
    print("RUNNING INTEGRATION TESTS")
    print("=" * 60)
    
    # Discover and run integration tests
    loader = unittest.TestLoader()
    start_dir = os.path.dirname(__file__)
    suite = loader.discover(start_dir, pattern='test_integration.py')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


def print_summary(unit_result, integration_result):
    """Print test summary"""
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    unit_total = unit_result.testsRun
    unit_failures = len(unit_result.failures)
    unit_errors = len(unit_result.errors)
    unit_passed = unit_total - unit_failures - unit_errors
    
    integration_total = integration_result.testsRun
    integration_failures = len(integration_result.failures)
    integration_errors = len(integration_result.errors)
    integration_passed = integration_total - integration_failures - integration_errors
    
    print(f"\nUnit Tests:")
    print(f"  Total:   {unit_total}")
    print(f"  Passed:  {unit_passed}")
    print(f"  Failed:  {unit_failures}")
    print(f"  Errors:  {unit_errors}")
    
    print(f"\nIntegration Tests:")
    print(f"  Total:   {integration_total}")
    print(f"  Passed:  {integration_passed}")
    print(f"  Failed:  {integration_failures}")
    print(f"  Errors:  {integration_errors}")
    
    total_tests = unit_total + integration_total
    total_passed = unit_passed + integration_passed
    total_failed = unit_failures + integration_failures
    total_errors = unit_errors + integration_errors
    
    print(f"\nOVERALL:")
    print(f"  Total:   {total_tests}")
    print(f"  Passed:  {total_passed}")
    print(f"  Failed:  {total_failed}")
    print(f"  Errors:  {total_errors}")
    
    if total_failed == 0 and total_errors == 0:
        print("\n✓ ALL TESTS PASSED!")
        return 0
    else:
        print("\n✗ SOME TESTS FAILED")
        return 1


def main():
    """Main test runner"""
    print("=" * 60)
    print("DURABLE FUNCTIONS WEB CRAWLER - TEST SUITE")
    print("=" * 60)
    
    # Run tests
    unit_result = run_unit_tests()
    integration_result = run_integration_tests()
    
    # Print summary and exit with appropriate code
    exit_code = print_summary(unit_result, integration_result)
    return exit_code


if __name__ == '__main__':
    sys.exit(main())
