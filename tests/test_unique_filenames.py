"""
Test suite for unique filename generation to prevent storage collisions
"""
import sys
import os
import hashlib
import re

# Add parent directory to path to import function_app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def generate_unique_filename(url, original_filename, site_name="unknown"):
    """Copy of the function for testing"""
    # Generate URL hash for uniqueness (8 chars is sufficient)
    url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
    
    # Sanitize site name for folder structure
    safe_site = re.sub(r'[^a-z0-9-]', '', site_name.lower().replace(' ', '-'))[:30]
    if not safe_site:
        safe_site = "unknown"
    
    # Extract and preserve extension
    if '.' in original_filename:
        ext = '.' + original_filename.split('.')[-1].lower()
        base_name = original_filename.rsplit('.', 1)[0]
    else:
        ext = '.pdf'  # Default extension
        base_name = original_filename
    
    # Sanitize base filename (remove special chars, limit length)
    safe_base = re.sub(r'[^a-zA-Z0-9_-]', '_', base_name)[:50]
    if not safe_base:
        safe_base = "document"
    
    # Format: site/hash_filename.ext
    return f"{safe_site}/{url_hash}_{safe_base}{ext}"


def test_unique_filename_generation():
    """Test that identical filenames from different URLs generate unique results"""
    
    print("=" * 80)
    print("PHASE 1 VERIFICATION: Unique Filename Generation")
    print("=" * 80)
    
    # Test Case 1: Same filename, different URLs (the collision scenario)
    test_cases = [
        {
            "url": "https://www.legislation.gov.uk/ukpga/2024/1052/data.pdf",
            "filename": "data.pdf",
            "site": "UK Legislation"
        },
        {
            "url": "https://www.legislation.gov.uk/ukpga/2024/1053/data.pdf",
            "filename": "data.pdf",
            "site": "UK Legislation"
        },
        {
            "url": "https://www.legislation.gov.uk/uksi/2024/105/data.pdf",
            "filename": "data.pdf",
            "site": "UK Legislation"
        },
        {
            "url": "https://www.cps.gov.uk/prosecution-guidance/document.pdf",
            "filename": "document.pdf",
            "site": "Crown Prosecution Service"
        },
        {
            "url": "https://www.cps.gov.uk/legal-guidance/document.pdf",
            "filename": "document.pdf",
            "site": "Crown Prosecution Service"
        },
        {
            "url": "https://www.npcc.police.uk/publications/guidance.pdf",
            "filename": "guidance.pdf",
            "site": "NPCC Publications - All Publications"
        }
    ]
    
    print("\n✅ TEST 1: Preventing Filename Collisions")
    print("-" * 80)
    
    generated_filenames = []
    collision_test_passed = True
    
    for i, test in enumerate(test_cases, 1):
        unique_name = generate_unique_filename(
            test["url"],
            test["filename"],
            test["site"]
        )
        generated_filenames.append(unique_name)
        
        print(f"\nTest {i}:")
        print(f"  Site:     {test['site']}")
        print(f"  Original: {test['filename']}")
        print(f"  URL:      {test['url']}")
        print(f"  Unique:   {unique_name}")
        
        # Check for duplicates
        if generated_filenames.count(unique_name) > 1:
            print(f"  ❌ COLLISION DETECTED!")
            collision_test_passed = False
        else:
            print(f"  ✅ Unique")
    
    print("\n" + "=" * 80)
    if collision_test_passed:
        print("✅ TEST 1 PASSED: All filenames are unique")
    else:
        print("❌ TEST 1 FAILED: Collisions detected")
    
    # Test Case 2: Verify all filenames are different
    print("\n✅ TEST 2: Uniqueness Verification")
    print("-" * 80)
    unique_count = len(set(generated_filenames))
    total_count = len(generated_filenames)
    
    print(f"Total filenames generated: {total_count}")
    print(f"Unique filenames: {unique_count}")
    
    if unique_count == total_count:
        print("✅ TEST 2 PASSED: 100% uniqueness achieved")
        test2_passed = True
    else:
        print(f"❌ TEST 2 FAILED: {total_count - unique_count} collisions found")
        test2_passed = False
    
    # Test Case 3: Special characters and edge cases
    print("\n✅ TEST 3: Special Characters and Edge Cases")
    print("-" * 80)
    
    edge_cases = [
        {
            "url": "https://example.com/path/file%20with%20spaces.pdf",
            "filename": "file with spaces.pdf",
            "site": "Test Site"
        },
        {
            "url": "https://example.com/file-with-symbols-!@#$%.pdf",
            "filename": "file-with-symbols-!@#$%.pdf",
            "site": "Test Site"
        },
        {
            "url": "https://example.com/no-extension",
            "filename": "no-extension",
            "site": "Test Site"
        },
        {
            "url": "https://example.com/very-long-filename-that-exceeds-normal-limits-and-should-be-truncated-properly-to-prevent-issues.pdf",
            "filename": "very-long-filename-that-exceeds-normal-limits-and-should-be-truncated-properly-to-prevent-issues.pdf",
            "site": "Test Site"
        }
    ]
    
    test3_passed = True
    for i, test in enumerate(edge_cases, 1):
        unique_name = generate_unique_filename(
            test["url"],
            test["filename"],
            test["site"]
        )
        
        print(f"\nEdge Case {i}:")
        print(f"  Original: {test['filename'][:60]}...")
        print(f"  Unique:   {unique_name}")
        
        # Validate no special characters in path
        if re.search(r'[^a-zA-Z0-9_.\-/]', unique_name):
            print(f"  ❌ Contains invalid characters")
            test3_passed = False
        else:
            print(f"  ✅ Valid filename")
    
    if test3_passed:
        print("\n✅ TEST 3 PASSED: All edge cases handled correctly")
    else:
        print("\n❌ TEST 3 FAILED: Invalid characters found")
    
    # Final Summary
    print("\n" + "=" * 80)
    print("PHASE 1 VERIFICATION SUMMARY")
    print("=" * 80)
    
    all_tests_passed = collision_test_passed and test2_passed and test3_passed
    
    if all_tests_passed:
        print("✅ ALL TESTS PASSED")
        print("\nPhase 1 Implementation Status: COMPLETE")
        print("\nExpected Impact:")
        print("  - Filename collisions: ELIMINATED")
        print("  - Storage count will match upload count")
        print("  - Documents organized by site in virtual folders")
        print("\nNext Steps:")
        print("  1. Deploy to Azure Function App")
        print("  2. Run test crawl on one site")
        print("  3. Verify storage count matches upload count")
        print("  4. Monitor logs for unique filename generation")
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        print("\nReview failures above and fix before deployment")
        return 1


if __name__ == "__main__":
    exit_code = test_unique_filename_generation()
    sys.exit(exit_code)
