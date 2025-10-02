"""
LinkedIn profile scraper using Apify SDK.

This module provides a function to fetch LinkedIn profiles in batch using
the Apify LinkedIn Profile Scraper actor.
"""

import os
from apify_client import ApifyClient
from dotenv import load_dotenv, find_dotenv

# Load environment variables
load_dotenv(find_dotenv('.env.local'))


def get_linkedin_profiles(linkedin_urls):
    """
    Fetch LinkedIn profiles from Apify API.

    Returns raw profile data exactly as Apify returns it.
    No processing, no filtering, no mapping.

    Args:
        linkedin_urls (list): List of full LinkedIn profile URLs
                             e.g., ["https://www.linkedin.com/in/artsofbaniya"]

    Returns:
        list: Raw profile dicts from Apify API response.
              May return fewer profiles than input URLs if some profiles
              are unavailable, private, or invalid.
              Empty list if API error occurs.

    Raises:
        Exception: If APIFY_API_TOKEN not set in environment
    """
    # Get credentials from environment
    api_token = os.getenv('APIFY_API_TOKEN')
    actor_id = os.getenv('APIFY_LINKEDIN_ACTOR_ID', '2SyF0bVxmgGr8IVCZ')

    if not api_token:
        raise Exception("APIFY_API_TOKEN not set in environment")

    # Initialize the ApifyClient with API token
    client = ApifyClient(api_token)

    # Prepare the Actor input (following Apify documentation pattern)
    run_input = {
        "profileUrls": linkedin_urls
    }

    print(f"Fetching {len(linkedin_urls)} LinkedIn profiles from Apify...")

    try:
        # Run the Actor and wait for it to finish
        run = client.actor(actor_id).call(run_input=run_input)
        print(f"Actor run completed. Run ID: {run.get('id')}")

        # Fetch Actor results from the run's dataset
        profiles = list(client.dataset(run["defaultDatasetId"]).iterate_items())

        print(f"Apify returned {len(profiles)} profiles")
        return profiles

    except Exception as e:
        print(f"Apify API error: {e}")
        return []


def get_single_linkedin_profile(linkedin_url):
    """
    Convenience function to fetch a single LinkedIn profile.

    Args:
        linkedin_url (str): Full LinkedIn profile URL

    Returns:
        dict: Profile dictionary or None if error
    """
    profiles = get_linkedin_profiles([linkedin_url])
    return profiles[0] if profiles else None
