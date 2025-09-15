"""
Simple health check script for Django app
"""

import sys
import urllib.request
import socket


def check_health():
    try:
        # Check if we can connect to the Django app
        response = urllib.request.urlopen("http://localhost:8000/_health/", timeout=10)
        if response.getcode() == 200:
            print("✅ Django app is healthy")
            return True
        else:
            print(f"❌ Django app returned status code: {response.getcode()}")
            return False
    except urllib.error.URLError as e:
        print(f"❌ Cannot reach Django app: {e}")
        return False
    except socket.timeout:
        print("❌ Django app health check timed out")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


if __name__ == "__main__":
    if check_health():
        sys.exit(0)
    else:
        sys.exit(1)
