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
    Fetch LinkedIn profiles using Apify LinkedIn Profile Scraper actor.

    Args:
        linkedin_urls (list): List of full LinkedIn profile URLs
                             e.g., ["https://www.linkedin.com/in/artsofbaniya"]

    Returns:
        list: List of profile dictionaries with fields like:
              - fullName, firstName, lastName
              - headline, about, connections, followers
              - urn (LinkedIn URN identifier)
              - experiences, skills, educations
              - etc.
              Returns empty list if error occurs.

    Raises:
        Exception: If Apify API token or actor ID not configured
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

    print(f"Calling Apify actor {actor_id} with {len(linkedin_urls)} profiles...")

    try:
        # Run the Actor and wait for it to finish
        run = client.actor(actor_id).call(run_input=run_input)

        print(f"Actor run completed. Run ID: {run.get('id')}")

        # Fetch Actor results from the run's dataset
        profiles = []
        dataset_id = run["defaultDatasetId"]

        print(f"Fetching results from dataset {dataset_id}...")

        for item in client.dataset(dataset_id).iterate_items():
            profiles.append(item)

        print(f"Successfully fetched {len(profiles)} profiles")
        return profiles

    except Exception as e:
        print(f"Error calling Apify actor: {e}")
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
