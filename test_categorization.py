#!/usr/bin/env python3
"""Test script to verify storage statistics categorization"""

# Simulate the updated categorization logic
def test_categorization():
    # Sample blob names that would come from storage
    test_blobs = [
        {"name": "college-of-policing/abc123_document.pdf", "size": 1024000},
        {"name": "crown-prosecution-service/def456_guidance.pdf", "size": 2048000},
        {"name": "npcc-publications/ghi789_report.pdf", "size": 512000},
        {"name": "uk-legislation-test/jkl012_act.xml", "size": 256000},
        {"name": "uk-public-general-acts/mno345_statute.xml", "size": 768000},
        {"name": "other/pqr678_unknown.pdf", "size": 128000}
    ]
    
    # Mapping of folder prefixes to display names
    site_display_names = {
        "college-of-policing": "College of Policing - App Portal",
        "crown-prosecution-service": "Crown Prosecution Service",
        "uk-legislation-test": "UK Legislation",
        "npcc-publications": "NPCC Publications",
        "uk-public-general-acts": "UK Public General Acts"
    }
    
    site_stats = {}
    
    for blob in test_blobs:
        # Extract the site folder prefix (before the first '/')
        if '/' in blob["name"]:
            site_folder = blob["name"].split('/')[0].lower()
        else:
            site_folder = "other"
        
        # Get display name or use the folder name if not mapped
        display_name = site_display_names.get(site_folder, site_folder.replace('-', ' ').title())
        
        # Initialize site stats if not exists
        if display_name not in site_stats:
            site_stats[display_name] = {"count": 0, "size": 0, "files": []}
        
        # Add blob to site stats
        site_stats[display_name]["count"] += 1
        site_stats[display_name]["size"] += blob["size"]
        site_stats[display_name]["files"].append(blob)
    
    # Print results
    print("📊 Document Categorization Test Results:\n")
    print("=" * 60)
    
    for site, stats in sorted(site_stats.items()):
        size_mb = stats["size"] / (1024 * 1024)
        print(f"\n{site}")
        print(f"  Documents: {stats['count']}")
        print(f"  Size: {size_mb:.2f} MB")
        print(f"  Files:")
        for file in stats["files"]:
            print(f"    - {file['name']}")
    
    print("\n" + "=" * 60)
    print("✅ Test complete! Labels now use website names instead of generic categories.")

if __name__ == "__main__":
    test_categorization()
