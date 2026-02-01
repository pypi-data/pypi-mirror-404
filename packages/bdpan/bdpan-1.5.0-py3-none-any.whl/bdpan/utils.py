from urllib.parse import urlparse, parse_qs 

def extract_params(url: str) -> dict[str, str]:
     """Extract query parameters from a URL into a dictionary."""
     parsed_url = urlparse(url)
     return {k: v[0] for k, v in parse_qs(parsed_url.query).items()}