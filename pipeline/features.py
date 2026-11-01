import re
import math

from collections import Counter

from utils import clean_url

SUSPICIOUS_WORDS = ["login", "signin", "verify", "account", "update", "secure",
                    "bank", "confirm", "password", "paypal", "free", "bonus"]
BRANDS = ["paypal", "apple", "microsoft", "office", "outlook", "amazon", "netflix",
          "google", "facebook", "instagram", "bank", "wellsfargo", "chase", "dhl",
          "ebay", "coinbase", "metamask", "steam", "whatsapp", "icloud"]
RISKY_TLDS = ["xyz", "top", "tk", "ml", "ga", "cf", "gq", "info", "ru", "cn",
              "click", "link", "online", "site", "live", "buzz", "icu", "cyou"]
RISKY_EXTENSIONS = ["exe", "apk", "zip", "rar", "scr", "dll", "bin", "sh", "jar", "msi"]


def entropy(text):
    """How random a string looks. 'google' = low, 'x7f9q2kz' = high."""
    if not text:
        return 0.0
    n = len(text)
    return -sum(c / n * math.log2(c / n) for c in Counter(text).values())


def split_url(url):
    """Split a URL into domain, path, file name and query.
    Done by hand because real-world malicious URLs are often malformed
    and would crash Python's standard URL parser."""
    u = clean_url(url)
    u, _, query = u.partition("?")
    u = u.split("#", 1)[0]
    host, slash, path = u.partition("/")
    path = slash + path
    domain = host.split("@")[-1].split(":")[0]   # drop user@ and :port
    last = path.rsplit("/", 1)[-1]
    filename = last if "." in last else ""
    return domain, path, filename, query


DELIMITERS = set("://.:/?=,;()]+")


def ratio(a, b):
    return len(a) / len(b) if b else 0.0


def digit_rate(text):
    """Share of characters that are digits ('Number Rate' in the paper)."""
    return sum(c.isdigit() for c in text) / len(text) if text else 0.0


def char_continuity_rate(text):
    """Longest run of letters + longest run of digits + longest run of symbols,
    divided by the length. Paper's example: abc567ti -> (3 + 3 + 1) / 9."""
    if not text:
        return 0.0
    runs = [max((len(m) for m in re.findall(p, text)), default=0)
            for p in (r"[a-z]+", r"[0-9]+", r"[^a-z0-9]+")]
    return sum(runs) / len(text)


def ldl_count(text):
    """Letter-digit-letter patterns like 'pa1pal' or 'cit1bank' (paper: ldl)."""
    return len(re.findall(r"(?=[a-z][0-9][a-z])", text))


def mamun_features(url):
    """The extra features named in Mamun et al. 2016, section 3.1 and Table 1."""
    u = clean_url(url)
    domain, path, filename, query = split_url(url)
    directory = path[: len(path) - len(filename)] if filename else path
    ext = filename.rsplit(".", 1)[-1] if filename else ""
    path_tokens = [t for t in re.split(r"[/.\-_]", path) if t]
    arg_words = [w for w in re.split(r"[=&]", query) if w]
    return {
        # ratios between URL parts (argPathRatio, argUrlRatio, ...)
        "arg_path_ratio": ratio(query, path),
        "arg_url_ratio": ratio(query, u),
        "arg_domain_ratio": ratio(query, domain),
        "domain_url_ratio": ratio(domain, u),
        "path_url_ratio": ratio(path, u),
        "path_domain_ratio": ratio(path, domain),
        # share of digits per part (NumberRate ...)
        "number_rate_domain": digit_rate(domain),
        "number_rate_directory": digit_rate(directory),
        "number_rate_filename": digit_rate(filename),
        "number_rate_url": digit_rate(u),
        "number_rate_after_path": digit_rate(query),
        # counts
        "domain_token_count": len([t for t in re.split(r"[.\-]", domain) if t]),
        "symbol_count_domain": sum(c in DELIMITERS for c in domain),
        "delimiter_path": sum(c in DELIMITERS for c in path),
        "dots_in_url": u.count("."),
        "query_digit_count": sum(c.isdigit() for c in query),
        "ldl_url": ldl_count(u),
        "ldl_path": ldl_count(path),
        # lengths
        "avg_path_token_length": (sum(map(len, path_tokens)) / len(path_tokens)
                                  if path_tokens else 0.0),
        "longest_path_token": max(map(len, path_tokens), default=0),
        "arg_longest_word": max(map(len, arg_words), default=0),
        # other
        "char_continuity_rate": char_continuity_rate(domain),
        "entropy_extension": entropy(ext),
    }


def get_features(url):
    u = clean_url(url)
    domain, path, filename, query = split_url(url)
    ext = filename.rsplit(".", 1)[-1] if filename else ""
    tokens = [t for t in re.split(r"[/.?=&\-_]", u) if t]
    return {
        # whole URL
        "url_length": len(u),
        "url_digits": sum(c.isdigit() for c in u),
        "url_letters": sum(c.isalpha() for c in u),
        "url_special_chars": len(re.findall(r"[^a-z0-9]", u)),
        "url_entropy": entropy(u),
        "url_tokens": len(tokens),
        "url_longest_token": max((len(t) for t in tokens), default=0),
        "url_suspicious_words": sum(w in u for w in SUSPICIOUS_WORDS),
        "has_at_sign": int("@" in url),
        "has_double_slash_in_path": int("//" in path),
        "percent_encoded": u.count("%"),
        # domain
        "domain_length": len(domain),
        "domain_dots": domain.count("."),
        "domain_hyphens": domain.count("-"),
        "domain_digits": sum(c.isdigit() for c in domain),
        "domain_entropy": entropy(domain),
        "domain_is_ip": int(bool(re.fullmatch(r"\d{1,3}(\.\d{1,3}){3}", domain))),
        "domain_has_port": int(":" in clean_url(url).split("/")[0]),
        "tld_length": len(domain.rsplit(".", 1)[-1]) if "." in domain else 0,
        "risky_tld": int(domain.rsplit(".", 1)[-1] in RISKY_TLDS),
        "brand_in_domain": int(any(b in domain for b in BRANDS)),
        "suspicious_words_in_domain": sum(w in domain for w in SUSPICIOUS_WORDS),
        # path
        "path_length": len(path),
        "path_depth": path.count("/"),
        "path_dots": path.count("."),
        "path_digits": sum(c.isdigit() for c in path),
        # file name
        "filename_length": len(filename),
        "risky_extension": int(ext in RISKY_EXTENSIONS),
        "php_or_html": int(ext in ("php", "html", "htm", "asp", "aspx")),
        # query arguments
        "query_length": len(query),
        "query_params": query.count("&") + (1 if query else 0),
        "query_equals": query.count("="),
        # the paper's extra features
        **mamun_features(url),
    }
