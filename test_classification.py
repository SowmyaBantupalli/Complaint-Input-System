"""
Test script to verify complaint classification improvements
Run this to test the extraction without deploying
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bns_classifier import get_classifier

# Test complaint from user
test_complaint = """Date: 5 January 2026
Yesterday at around 8:30 PM, my motorcycle was stolen from outside my apartment in Andheri East, Mumbai. I had parked it near the gate. When I returned, it was missing. I suspect someone from the nearby area may have taken it.

Name: Ramesh Sharma"""

print("=" * 70)
print("TESTING COMPLAINT CLASSIFICATION")
print("=" * 70)
print("\nINPUT COMPLAINT:")
print("-" * 70)
print(test_complaint)
print("-" * 70)

print("\nINITIALIZING CLASSIFIER...")
classifier = get_classifier()

if classifier.is_initialized:
    print("✅ Gemini AI Active - Using AI Classification")
else:
    print("⚠️  Gemini Not Configured - Using Enhanced Fallback")

print("\nANALYZING...")
result = classifier.classify_complaint(test_complaint)

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

if result.get('additional_notes'):
    print(f"\nAdditional Notes:")
    print(f"  {result['additional_notes']}")

print(f"\nAI Classification: {'Yes' if result.get('ai_classification') else 'No (Fallback)'}")
print("=" * 70)

# Verify expected results
print("\n" + "=" * 70)
print("VERIFICATION:")
print("=" * 70)
errors = []

if result.get('crime_type') != 'Theft':
    errors.append(f"❌ Crime Type should be 'Theft', got '{result.get('crime_type')}'")
else:
    print("✅ Crime Type: Correct")

if 'Andheri' not in result.get('location', '') or 'Mumbai' not in result.get('location', ''):
    errors.append(f"❌ Location should contain 'Andheri East, Mumbai', got '{result.get('location')}'")
else:
    print("✅ Location: Correct")

if result.get('time') != '8:30 PM' and 'around 8:30 PM' not in result.get('time', ''):
    errors.append(f"❌ Time should be '8:30 PM', got '{result.get('time')}'")
else:
    print("✅ Time: Correct")

if result.get('date') == 'Not Specified':
    errors.append(f"❌ Date should be extracted, got '{result.get('date')}'")
else:
    print("✅ Date: Correct")

if 'Ramesh' not in result.get('persons_involved', '') and result.get('persons_involved') == 'Not Specified':
    errors.append(f"❌ Persons should contain 'Ramesh Sharma', got '{result.get('persons_involved')}'")
else:
    print("✅ Persons: Correct")

if '303' not in result.get('predicted_section', ''):
    errors.append(f"❌ Section should contain '303', got '{result.get('predicted_section')}'")
else:
    print("✅ Legal Section: Correct")

if errors:
    print("\n⚠️  ISSUES FOUND:")
    for error in errors:
        print(f"  {error}")
    print(f"\nℹ️  If Gemini is not configured, some extraction may be limited.")
    print(f"   Set GEMINI_API_KEY environment variable for best results.")
else:
    print("\n🎉 ALL CHECKS PASSED! Classification working correctly.")

print("=" * 70)
