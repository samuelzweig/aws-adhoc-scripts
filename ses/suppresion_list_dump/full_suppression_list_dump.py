"""This script dumps all email addresses in your account suppression list.

You might be able to get away with less aggressive rate limiting. I am erring
on the side of extreme caution here since AWS throttles some API calls on a per-region
basis. I do not want some other critical application throwing throttling exceptions
because I ran this script.
"""

from typing import Iterator
from ratelimit import limits, sleep_and_retry
import boto3


def full_suppression_list_dump(
        rate_limit_period=3,
        calls_per_period=1) -> Iterator[str]:
    """Paginates through ListSuppressedDestinations yielding results"""

    @sleep_and_retry
    @limits(calls=calls_per_period, period=rate_limit_period)
    def get_page(**kwargs) -> []:
        """Make one call to the ListSuppressedDestinations AWS SDK endpoint"""
        nonlocal sesv2_client
        response = sesv2_client.list_suppressed_destinations(**kwargs)
        if "NextToken" not in response:
            return None
        return response

    sesv2_client = boto3.client("sesv2")

    kwargs = {"Reasons": ["BOUNCE", "COMPLAINT"]}
    done = False
    while not done:
        response = get_page(**kwargs)
        for item in response["SuppressedDestinationSummaries"]:
            yield item["EmailAddress"]
        if "NextToken" not in response:
            done = True
        else:
            kwargs["NextToken"] = response["NextToken"]


def main():
    """write all email addresses in the suppresion list to stdout"""
    for email_addresses in full_suppression_list_dump():
        print(email_addresses)


if __name__ == "__main__":
    main()
