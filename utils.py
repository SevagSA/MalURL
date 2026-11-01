import re

def clean_url(url):
    """Normalizes URL and removes protocols and www."""
    url = url.strip().lower()
    url = re.sub(r"^[a-z]+://", "", url)
    url = re.sub(r"^www\.", "", url)
    return url.rstrip("/")