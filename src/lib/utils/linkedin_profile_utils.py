"""
LinkedIn profile processing utilities.

Functions for processing raw Apify profile data and matching to guests.
"""

import json


def normalize_linkedin_handle(linkedin_url_or_handle):
    """
    Normalize LinkedIn handle to /in/<handle> format for comparison.

    Examples:
        "https://linkedin.com/in/artsofbaniya/" → "/in/artsofbaniya"
        "/in/ArtsOfBaniya" → "/in/artsofbaniya"
        "artsofbaniya" → "/in/artsofbaniya"

    Args:
        linkedin_url_or_handle: LinkedIn URL, /in/ path, or just the handle

    Returns:
        str: Normalized format /in/<handle> in lowercase
    """
    # Remove URL prefixes if present
    handle = linkedin_url_or_handle.replace('https://www.linkedin.com', '')
    handle = handle.replace('https://linkedin.com', '')
    handle = handle.replace('http://www.linkedin.com', '')
    handle = handle.strip('/')

    # Ensure /in/ prefix
    if not handle.startswith('in/'):
        handle = f'in/{handle}'

    # Add leading slash and lowercase
    return f'/{handle}'.lower()


def create_lookup_from_apify_profiles(apify_profiles):
    """
    Index Apify profiles by LinkedIn handle for fast lookup.

    Args:
        apify_profiles: Raw profile list from Apify API

    Returns:
        dict: {linkedin_handle: apify_profile_dict}
              e.g., {"/in/artsofbaniya": {...profile_data...}}
    """
    handle_to_profile = {}
    for profile in apify_profiles:
        public_id = profile.get('publicIdentifier', '')
        if public_id:
            normalized_handle = normalize_linkedin_handle(public_id)
            handle_to_profile[normalized_handle] = profile
    return handle_to_profile


def match_guest_to_apify_profile(guest_record, apify_profile_lookup):
    """
    Find Apify profile for a specific guest.

    Args:
        guest_record: Tuple of (luma_guest_api_id, guest_name, linkedin_handle[, retry_count])
        apify_profile_lookup: Dict from create_lookup_from_apify_profiles()

    Returns:
        dict or None: Apify profile if found, None if unavailable
    """
    # Handle both 3-tuple and 4-tuple formats
    linkedin_handle = guest_record[2]
    normalized_handle = normalize_linkedin_handle(linkedin_handle)
    return apify_profile_lookup.get(normalized_handle)


def partition_guests_by_profile_availability(pending_guests, apify_profile_lookup):
    """
    Split guests by whether Apify returned their profile.

    Args:
        pending_guests: List of guest tuples needing enrichment
        apify_profile_lookup: Handle → profile dict

    Returns:
        tuple: (guests_with_profiles, guests_without_profiles)
            guests_with_profiles: [(apify_profile_dict, guest_record), ...]
            guests_without_profiles: [guest_record, ...]
    """
    with_profiles = []
    without_profiles = []

    for guest in pending_guests:
        apify_profile = match_guest_to_apify_profile(guest, apify_profile_lookup)
        if apify_profile:
            with_profiles.append((apify_profile, guest))
        else:
            without_profiles.append(guest)

    return with_profiles, without_profiles


def build_enriched_profile_record(apify_profile, guest_record):
    """
    Transform Apify profile into database record format.

    Args:
        apify_profile: Raw profile dict from Apify
        guest_record: Tuple of (luma_guest_api_id, guest_name, linkedin_handle[, retry_count])

    Returns:
        tuple: Complete database record with all fields populated
    """
    # Handle both 3-tuple and 4-tuple formats
    luma_guest_api_id = guest_record[0]
    guest_name = guest_record[1]
    linkedin_handle = guest_record[2]

    return (
        luma_guest_api_id,
        linkedin_handle,
        'apify',  # record_source
        True,     # profile_found
        None,     # profile_fetch_message
        apify_profile.get('fullName'),
        apify_profile.get('firstName'),
        apify_profile.get('lastName'),
        apify_profile.get('headline'),
        apify_profile.get('about'),
        apify_profile.get('publicIdentifier'),
        apify_profile.get('linkedinUrl'),
        apify_profile.get('connections'),
        apify_profile.get('followers'),
        apify_profile.get('jobTitle'),
        apify_profile.get('companyName'),
        apify_profile.get('companyIndustry'),
        apify_profile.get('companyWebsite'),
        apify_profile.get('companyLinkedin'),
        apify_profile.get('companyFoundedIn'),
        apify_profile.get('companySize'),
        apify_profile.get('currentJobDurationInYrs'),
        apify_profile.get('addressWithCountry'),
        apify_profile.get('addressCountryOnly'),
        apify_profile.get('addressWithoutCountry'),
        apify_profile.get('profilePic'),
        apify_profile.get('profilePicHighQuality'),
        apify_profile.get('topSkillsByEndorsements'),
        json.dumps(apify_profile),  # profile_data JSONB
        0,     # retry_count (reset to 0 on success)
        None,  # last_retry_at (clear on success)
        None,  # next_retry_after (clear on success)
    )


def build_missing_profile_record(guest_record, current_retry_count=0):
    """
    Create record for guest with no available LinkedIn profile.

    Args:
        guest_record: Tuple of (luma_guest_api_id, guest_name, linkedin_handle, retry_count)
        current_retry_count: Current retry count from database (default 0 for new records)

    Returns:
        tuple: Database record marking profile as not found with retry tracking
    """
    # Unpack guest record (may have 3 or 4 fields depending on source)
    if len(guest_record) == 4:
        luma_guest_api_id, guest_name, linkedin_handle, db_retry_count = guest_record
        current_retry_count = db_retry_count or 0
    else:
        luma_guest_api_id, guest_name, linkedin_handle = guest_record

    import time
    current_timestamp = int(time.time() * 1000)  # epoch milliseconds
    new_retry_count = current_retry_count + 1

    # Exponential backoff: 5min, 20min, 45min (retry_count^2 * 5 minutes)
    backoff_minutes = (new_retry_count ** 2) * 5
    next_retry_timestamp = current_timestamp + (backoff_minutes * 60 * 1000)

    return (
        luma_guest_api_id,
        linkedin_handle,
        'apify',  # record_source
        False,    # profile_found
        'Profile not returned by Apify API',  # profile_fetch_message
        *([None] * 23),  # 23 None values for profile fields (full_name through top_skills_by_endorsements)
        None,  # profile_data JSONB
        new_retry_count,  # retry_count (incremented)
        current_timestamp,  # last_retry_at
        next_retry_timestamp,  # next_retry_after (exponential backoff)
    )
