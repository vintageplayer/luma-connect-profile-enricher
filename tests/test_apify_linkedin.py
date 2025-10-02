"""Test Apify LinkedIn scraper with URN validation."""

import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from lib.apify import get_linkedin_profiles, get_single_linkedin_profile


# Expected test data
EXPECTED_PROFILES = {
    "artsofbaniya": {
        "url": "https://www.linkedin.com/in/artsofbaniya",
        "urn": "ACoAABox-DgBv7Mi3aWbDPO2YFEajv0DguzfTLA",
        "name": "Aditya Agarwal"
    },
    "alanagoyal": {
        "url": "https://www.linkedin.com/in/alanagoyal",
        "urn": "ACoAABjYMpUBxFR-CCjyVDu2TqHeJ3-c3hKxv5Y",
        "name": "alana goyal"
    }
}


def test_single_profile():
    """Test fetching a single LinkedIn profile."""
    print("=" * 60)
    print("Test 1: Single Profile Fetch")
    print("=" * 60)

    test_case = EXPECTED_PROFILES["artsofbaniya"]
    url = test_case["url"]
    expected_urn = test_case["urn"]

    print(f"Fetching profile: {url}")
    profile = get_single_linkedin_profile(url)

    if not profile:
        print("❌ FAILED: No profile returned")
        return False

    actual_urn = profile.get('urn')
    full_name = profile.get('fullName')

    print(f"\nProfile Data:")
    print(f"  Full Name: {full_name}")
    print(f"  URN: {actual_urn}")
    print(f"  Expected URN: {expected_urn}")
    print(f"  Headline: {profile.get('headline')}")
    print(f"  Connections: {profile.get('connections')}")

    if actual_urn == expected_urn:
        print(f"\n✅ PASSED: URN matches!")
        return True
    else:
        print(f"\n❌ FAILED: URN mismatch")
        return False


def test_batch_profiles():
    """Test fetching multiple profiles in batch."""
    print("\n" + "=" * 60)
    print("Test 2: Batch Profile Fetch")
    print("=" * 60)

    urls = [
        EXPECTED_PROFILES["artsofbaniya"]["url"],
        EXPECTED_PROFILES["alanagoyal"]["url"]
    ]

    print(f"Fetching {len(urls)} profiles in batch...")
    profiles = get_linkedin_profiles(urls)

    if len(profiles) != len(urls):
        print(f"❌ FAILED: Expected {len(urls)} profiles, got {len(profiles)}")
        return False

    print(f"\nFetched {len(profiles)} profiles:\n")

    all_passed = True
    for profile in profiles:
        public_id = profile.get('publicIdentifier')
        actual_urn = profile.get('urn')
        full_name = profile.get('fullName')

        # Find expected URN
        expected = EXPECTED_PROFILES.get(public_id, {})
        expected_urn = expected.get('urn')

        print(f"Profile: {full_name} ({public_id})")
        print(f"  URN: {actual_urn}")
        print(f"  Expected URN: {expected_urn}")

        if actual_urn == expected_urn:
            print(f"  ✅ URN matches")
        else:
            print(f"  ❌ URN mismatch")
            all_passed = False
        print()

    if all_passed:
        print("✅ PASSED: All URNs match!")
        return True
    else:
        print("❌ FAILED: Some URNs don't match")
        return False


def run_all_tests():
    """Run all tests and report summary."""
    print("\n" + "=" * 60)
    print("APIFY LINKEDIN SCRAPER TESTS")
    print("=" * 60 + "\n")

    results = []

    # Test 1: Single profile
    try:
        results.append(("Single Profile", test_single_profile()))
    except Exception as e:
        print(f"❌ Test 1 EXCEPTION: {e}")
        results.append(("Single Profile", False))

    # Test 2: Batch profiles
    try:
        results.append(("Batch Profiles", test_batch_profiles()))
    except Exception as e:
        print(f"❌ Test 2 EXCEPTION: {e}")
        results.append(("Batch Profiles", False))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")

    print(f"\nTotal: {passed}/{total} tests passed")
    print("=" * 60 + "\n")

    return passed == total


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
