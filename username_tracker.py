"""
username_tracker.py
Resilient username lookup module for GhostTrack.
Provides individual error catching, timeout handling, and status categorization.
"""

from typing import Callable, Dict, List, Optional
import requests

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

# Cleaned list of platforms (deduplicated Snapchat and removed defunct platforms)
DEFAULT_SITES: List[Dict[str, str]] = [
    {"url": "https://www.facebook.com/{}", "name": "Facebook"},
    {"url": "https://www.twitter.com/{}", "name": "Twitter"},
    {"url": "https://www.instagram.com/{}", "name": "Instagram"},
    {"url": "https://www.linkedin.com/in/{}", "name": "LinkedIn"},
    {"url": "https://www.github.com/{}", "name": "GitHub"},
    {"url": "https://www.pinterest.com/{}", "name": "Pinterest"},
    {"url": "https://www.tumblr.com/{}", "name": "Tumblr"},
    {"url": "https://www.youtube.com/{}", "name": "Youtube"},
    {"url": "https://soundcloud.com/{}", "name": "SoundCloud"},
    {"url": "https://www.snapchat.com/add/{}", "name": "Snapchat"},
    {"url": "https://www.tiktok.com/@{}", "name": "TikTok"},
    {"url": "https://www.behance.net/{}", "name": "Behance"},
    {"url": "https://www.medium.com/@{}", "name": "Medium"},
    {"url": "https://www.quora.com/profile/{}", "name": "Quora"},
    {"url": "https://www.flickr.com/people/{}", "name": "Flickr"},
    {"url": "https://www.twitch.tv/{}", "name": "Twitch"},
    {"url": "https://dribbble.com/{}", "name": "Dribbble"},
    {"url": "https://www.producthunt.com/@{}", "name": "Product Hunt"},
    {"url": "https://t.me/{}", "name": "Telegram"},
    {"url": "https://weheartit.com/{}", "name": "We Heart It"},
]


def check_site(
    site: Dict[str, str],
    username: str,
    timeout: float = 5.0,
    headers: Optional[Dict[str, str]] = None,
) -> Dict[str, str]:
    """Check if a username exists on a specific platform.

    Catches all network and HTTP errors per site so a single failure never
    aborts the entire search.
    """
    url = site["url"].format(username)
    site_name = site["name"]
    req_headers = {"User-Agent": DEFAULT_USER_AGENT}
    if headers:
        req_headers.update(headers)

    try:
        response = requests.get(
            url, headers=req_headers, timeout=timeout, allow_redirects=True
        )
        code = response.status_code

        if code == 200:
            return {
                "name": site_name,
                "status": "FOUND",
                "url": url,
                "message": "Found",
                "status_code": code,
            }
        elif code == 404:
            return {
                "name": site_name,
                "status": "NOT_FOUND",
                "url": url,
                "message": "Username not found",
                "status_code": code,
            }
        elif code in (401, 403, 429):
            return {
                "name": site_name,
                "status": "BLOCKED",
                "url": url,
                "message": f"Access restricted / rate-limited (HTTP {code})",
                "status_code": code,
            }
        else:
            return {
                "name": site_name,
                "status": "ERROR",
                "url": url,
                "message": f"Server response HTTP {code}",
                "status_code": code,
            }

    except requests.exceptions.Timeout:
        return {
            "name": site_name,
            "status": "TIMEOUT",
            "url": url,
            "message": f"Connection timed out (>{timeout}s)",
            "status_code": None,
        }
    except requests.exceptions.ConnectionError:
        return {
            "name": site_name,
            "status": "ERROR",
            "url": url,
            "message": "Connection error / Unreachable",
            "status_code": None,
        }
    except requests.exceptions.RequestException as e:
        return {
            "name": site_name,
            "status": "ERROR",
            "url": url,
            "message": f"Request failed: {type(e).__name__}",
            "status_code": None,
        }
    except Exception as e:
        return {
            "name": site_name,
            "status": "ERROR",
            "url": url,
            "message": f"Unexpected error: {str(e)}",
            "status_code": None,
        }


def search_username(
    username: str,
    sites: Optional[List[Dict[str, str]]] = None,
    timeout: float = 5.0,
    callback: Optional[Callable[[Dict[str, str]], None]] = None,
) -> List[Dict[str, str]]:
    """Search for a username across multiple platforms sequentially or with a callback.

    Guarantees every site is processed and no exception can terminate the batch.
    """
    target_sites = sites if sites is not None else DEFAULT_SITES
    results = []

    for site in target_sites:
        res = check_site(site, username, timeout=timeout)
        results.append(res)
        if callback:
            try:
                callback(res)
            except Exception:
                pass

    return results
