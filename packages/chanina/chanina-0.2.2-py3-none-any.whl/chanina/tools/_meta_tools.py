""" Well ... These are tools for the tools.
"""
import time

from playwright.sync_api import ElementHandle, Locator, Page


def normalize_url(raw_url: str) -> str:
    """ Returns a normalized url from the raw_url passed. It doesn't mean that the url will work. """
    url = raw_url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    if not url.endswith("/"):
        url += "/"
    return url


def wait_for_n_elements(page: Page, n: int, selector: str, timeout: float = 5000) -> list:
    """
    Wait till the DOM has loaded at least 'n' before timeout, then returns the select_all,
    or timeout if 'n' elements weren't found.

    Args:
        - page (Playwright.Page): page to search in.
        - n (int): minimum number of elements that should be returned.
        - selector (str): html selector.
        - timeout (int): time in ms before raising exception.
    """
    timeout /= 1000
    nw = time.time()
    while len(page.query_selector_all(selector)) <= n:
        time.sleep(0.1)
        if time.time() >= nw + timeout:
            raise TimeoutError(f"timed out fetching {n} elements with selector '{selector}'.")
    return page.query_selector_all(selector)


def ensure_one_locator(obj, page) -> Locator:
    """ Take a playwright object return type and make it a locator. """
    if isinstance(obj, Locator):
        return obj
    elif isinstance(obj, ElementHandle):
        selector = obj.evaluate("el => el.tagName.toLowerCase()")
        return page.locator(selector)
    else:
        raise TypeError(f"Unsupported return type for : {obj}")


def ensure_locators(obj, page) -> list[Locator]:
    """ Take multiple playwright objects return types and make it a list of locators. """
    r = set()
    if isinstance(obj, list):
        selectors = set()
        for o in obj:
            selectors.add(o.evaluate("el => el.tagName.toLowerCase()"))
        for s in selectors:
            loc = page.locator(s)
            for i in range(loc.count()):
                r.add(loc.nth(i))
    elif isinstance(obj, Locator):
        r.add(obj)
    elif isinstance(obj, ElementHandle):
        r.add(ensure_one_locator(obj, page))
    else:
        raise TypeError(f"Could not ensure à Locator return type for {obj}")
    return list(r)
