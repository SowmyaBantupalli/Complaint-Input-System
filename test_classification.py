"""
Test script to verify complaint classification improvements
Run this to test the extraction without deploying
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bns_classifier import get_classifier

# Test complaints
test_complaints = [
    {
        "name": "Test 1: Motorcycle Theft",
        "text": """Date: 5 January 2026
Yesterday at around 8:30 PM, my motorcycle was stolen from outside my apartment in Andheri East, Mumbai. I had parked it near the gate. When I returned, it was missing. I suspect someone from the nearby area may have taken it.

Name: Ramesh Sharma""",
        "expected": {
            "crime_type": "Theft",
            "location_contains": ["Andheri", "Mumbai"],
            "time": "8:30 PM",
            "date_not": "Not Specified",
            "persons_contains": "Ramesh",
            "section_contains": "303"
        }
    },
    {
        "name": "Test 2: Grievous Hurt with Weapon",
        "text": """Date: 9 April 2026
On 8 April 2026 at 8 PM near the railway station in Lucknow, I was attacked with a metal rod and my arm was fractured.

Name: Imran Khan""",
        "expected": {
            "crime_type": "Grievous Hurt",
            "location_contains": ["railway station", "Lucknow"],
            "location_not_contains": "8 PM",
            "time": "8 PM",
            "date_contains": "8 April",
            "persons_contains": "Imran",
            "section_contains": "116",  # or 118 for weapon
            "severity": "High"
        }
    }
]

print("=" * 70)
print("TESTING COMPLAINT CLASSIFICATION - MULTIPLE CASES")
print("=" * 70)

print("\nINITIALIZING CLASSIFIER...")
classifier = get_classifier()

if classifier.is_initialized:
    print("✅ Gemini AI Active - Using AI Classification")
else:
    print("⚠️  Gemini Not Configured - Using Enhanced Fallback")

all_passed = True

for test_case in test_complaints:
    print("\n" + "=" * 70)
    print(f"TEST: {test_case['name']}")
    print("=" * 70)
    print("\nINPUT COMPLAINT:")
    print("-" * 70)
    print(test_case['text'])
    print("-" * 70)
    
    print("\nANALYZING...")
    result = classifier.classify_complaint(test_case['text'])
    
    print("\n" + "=" * 70)
    print("EXTRACTED INFORMATION:")
    print("=" * 70)
    print(f"Crime Type:         {result.get('crime_type', 'N/A')}")
    print(f"Location:          {result.get('location', 'N/A')}")
    print(f"Date:              {result.get('date', 'N/A')}")
    print(f"Time:              {result.get('time', 'N/A')}")
    print(f"Persons Involved:  {result.get('persons_involved', 'N/A')}")
    print(f"Legal Section:     {result.get('predicted_section', 'N/A')}")
    print(f"Severity:          {result.get('severity', 'N/A')}")
    print(f"\nKey Event Summary:")
    print(f"  {result.get('key_event_summary', 'N/A')}")
    
    if result.get('bns_sections'):
        print(f"\nBNS Sections:")
        for sec in result['bns_sections']:
            if isinstance(sec, dict):
                print(f"  - Section {sec.get('section', 'N/A')}: {sec.get('reason', 'N/A')}")
    
    # Verification
    print("\n" + "=" * 70)
    print("VERIFICATION:")
    print("=" * 70)
    errors = []
    expected = test_case['expected']
    
    # Check crime type
    if expected.get('crime_type') and result.get('crime_type') != expected['crime_type']:
        errors.append(f"❌ Crime Type: Expected '{expected['crime_type']}', got '{result.get('crime_type')}'")
    else:
        print(f"✅ Crime Type: {result.get('crime_type')}")
    
    # Check location
    location = result.get('location', '')
    if expected.get('location_contains'):
        if all(term in location for term in expected['location_contains']):
            print(f"✅ Location: {location}")
        else:
            errors.append(f"❌ Location should contain {expected['location_contains']}, got '{location}'")
    
    if expected.get('location_not_contains'):
        if expected['location_not_contains'] not in location:
            print(f"✅ Location correctly excludes time")
        else:
            errors.append(f"❌ Location should NOT contain '{expected['location_not_contains']}', got '{location}'")
    
    # Check time
    if expected.get('time'):
        if expected['time'] in result.get('time', ''):
            print(f"✅ Time: {result.get('time')}")
        else:
            errors.append(f"❌ Time: Expected '{expected['time']}', got '{result.get('time')}'")
    
    # Check date
    if expected.get('date_not'):
        if result.get('date') != expected['date_not']:
            print(f"✅ Date: {result.get('date')}")
        else:
            errors.append(f"❌ Date should be extracted, got '{result.get('date')}'")
    
    if expected.get('date_contains'):
        if expected['date_contains'] in result.get('date', ''):
            print(f"✅ Date: {result.get('date')}")
        else:
            errors.append(f"❌ Date should contain '{expected['date_contains']}', got '{result.get('date')}'")
    
    # Check persons
    if expected.get('persons_contains'):
        if expected['persons_contains'] in result.get('persons_involved', ''):
            print(f"✅ Persons: {result.get('persons_involved')}")
        else:
            errors.append(f"❌ Persons should contain '{expected['persons_contains']}', got '{result.get('persons_involved')}'")
    
    # Check section
    if expected.get('section_contains'):
        section_str = result.get('predicted_section', '')
        if expected['section_contains'] in section_str or any(
            expected['section_contains'] in str(s.get('section', '')) 
            for s in result.get('bns_sections', []) if isinstance(s, dict)
        ):
            print(f"✅ Legal Section: {section_str}")
        else:
            errors.append(f"❌ Section should contain '{expected['section_contains']}', got '{section_str}'")
    
    # Check severity
    if expected.get('severity'):
        if result.get('severity') == expected['severity']:
            print(f"✅ Severity: {result.get('severity')}")
        else:
            errors.append(f"❌ Severity: Expected '{expected['severity']}', got '{result.get('severity')}'")
    
    if errors:
        print("\n⚠️  ISSUES FOUND:")
        for error in errors:
            print(f"  {error}")
        all_passed = False
    else:
        print("\n🎉 ALL CHECKS PASSED for this test!")
    
    print("=" * 70)

print("\n" + "=" * 70)
print("FINAL RESULT:")
print("=" * 70)
if all_passed:
    print("🎉 ALL TESTS PASSED! Classification working correctly.")
else:
    print("⚠️  Some tests failed. Review issues above.")
    if not classifier.is_initialized:
        print("ℹ️  Configure GEMINI_API_KEY for better accuracy.")
print("=" * 70)
