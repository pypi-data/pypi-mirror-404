import logging
from chanina.tools._meta_tools import ensure_locators, wait_for_n_elements

from playwright.sync_api import Locator


class Inspect:
    def __init__(self, session) -> None:
        self.session = session

    def get_by_selector(
        self,
        selector: str,
        n_min: int = 1,
        timeout: int = 5000
    ) -> list[Locator]:
        """ Get all loaded items on the page with the specified selector. """
        elements = wait_for_n_elements(self.session.current_page, n_min, selector, timeout=timeout)
        return ensure_locators(elements, self.session.current_page)
    
    def get_by_content_text(
        self,
        text: str,
        selector: str = "div",
        strict: bool = False,
        n_min: int = 0,
        timeout: int = 2000
    ) -> list[Locator]:
        """
        Get a list of Locator(s) which contains the 'text' arguments.
        Be careful, technically, if you have a span with your text argument,
        inside a div and inside another div, they will all get appended to the list.
    
        Args:
            - text (str): the string that should match.
            - selector (str): tag in which the search is made. Can be set to "*" for global search.
            - strict (bool): if True returns element strictly matching string.
            - n_min (int): minimum elements to wait for (raise exception if less)
        """
        if selector == "*":
            logging.warning(f"selector is set to '*', this can slow the runtime a lot.")
        elements = wait_for_n_elements(page=self.session.current_page, n=n_min, selector=selector, timeout=timeout)
        if strict:
            return ensure_locators([el for el in elements if el.text_content() == text], self.session.current_page)
        return ensure_locators([el for el in elements if text in el.text_content()], self.session.current_page)
