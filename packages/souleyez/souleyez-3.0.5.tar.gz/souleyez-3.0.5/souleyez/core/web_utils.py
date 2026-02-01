"""
Web utility functions for SoulEyez.

Includes HTTP redirect detection and other web-related helpers.
"""

from typing import Dict, Optional
from urllib.parse import urlparse

import requests


def check_http_redirect(ip: str, port: int = 80, timeout: int = 3) -> Dict[str, any]:
    """
    Check if HTTP redirects to HTTPS.

    This function makes a HEAD request to the HTTP endpoint and follows redirects
    to determine if the server automatically upgrades to HTTPS. This is used to
    avoid redundant scans when HTTP and HTTPS serve identical content.

    Args:
        ip: IP address or hostname to check
        port: HTTP port to check (default: 80)
        timeout: Request timeout in seconds (default: 3)

    Returns:
        Dictionary with redirect information:
        {
            'redirects_to_https': bool,  # True if final URL is HTTPS
            'final_scheme': str,          # 'http' or 'https'
            'final_url': str or None,     # Final URL after redirects
            'status_code': int or None,   # HTTP status code
            'error': str or None          # Error message if request failed
        }

    Example:
        >>> check_http_redirect('example.com')
        {'redirects_to_https': True, 'final_scheme': 'https',
         'final_url': 'https://example.com/', 'status_code': 200, 'error': None}
    """
    result = {
        "redirects_to_https": False,
        "final_scheme": "http",
        "final_url": None,
        "status_code": None,
        "error": None,
    }

    url = f"http://{ip}:{port}/"

    try:
        # Make HEAD request with redirect following
        # verify=False for self-signed certs (pentesting context)
        # allow_redirects=True to follow redirect chain (max 30 by default)
        response = requests.head(
            url,
            timeout=timeout,
            verify=False,  # nosec B501 - pentesting tool needs to handle self-signed certs
            allow_redirects=True,
            headers={"User-Agent": "SoulEyez/1.0"},
        )

        # Get final URL after all redirects
        final_url = response.url
        result["final_url"] = final_url
        result["status_code"] = response.status_code

        # Parse final URL to get scheme
        parsed = urlparse(final_url)
        result["final_scheme"] = parsed.scheme

        # Check if we ended up on HTTPS
        if parsed.scheme == "https":
            result["redirects_to_https"] = True

    except requests.exceptions.Timeout:
        result["error"] = f"Timeout after {timeout}s"
    except requests.exceptions.SSLError as e:
        result["error"] = f"SSL error: {str(e)[:100]}"
    except requests.exceptions.ConnectionError as e:
        result["error"] = f"Connection error: {str(e)[:100]}"
    except requests.exceptions.RequestException as e:
        result["error"] = f"Request error: {str(e)[:100]}"
    except Exception as e:
        result["error"] = f"Unexpected error: {str(e)[:100]}"

    return result


def check_https_redirect(ip: str, port: int = 443, timeout: int = 3) -> Dict[str, any]:
    """
    Check if HTTPS redirects to HTTP (rare, but possible).

    Similar to check_http_redirect but for HTTPS endpoints.

    Args:
        ip: IP address or hostname to check
        port: HTTPS port to check (default: 443)
        timeout: Request timeout in seconds (default: 3)

    Returns:
        Dictionary with redirect information (same format as check_http_redirect)
    """
    result = {
        "redirects_to_http": False,
        "final_scheme": "https",
        "final_url": None,
        "status_code": None,
        "error": None,
    }

    url = f"https://{ip}:{port}/"

    try:
        response = requests.head(
            url,
            timeout=timeout,
            verify=False,  # nosec B501 - pentesting tool needs to handle self-signed certs
            allow_redirects=True,
            headers={"User-Agent": "SoulEyez/1.0"},
        )

        final_url = response.url
        result["final_url"] = final_url
        result["status_code"] = response.status_code

        parsed = urlparse(final_url)
        result["final_scheme"] = parsed.scheme

        if parsed.scheme == "http":
            result["redirects_to_http"] = True

    except requests.exceptions.Timeout:
        result["error"] = f"Timeout after {timeout}s"
    except requests.exceptions.SSLError as e:
        result["error"] = f"SSL error: {str(e)[:100]}"
    except requests.exceptions.ConnectionError as e:
        result["error"] = f"Connection error: {str(e)[:100]}"
    except requests.exceptions.RequestException as e:
        result["error"] = f"Request error: {str(e)[:100]}"
    except Exception as e:
        result["error"] = f"Unexpected error: {str(e)[:100]}"

    return result


# Suppress SSL warnings for pentesting context
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
