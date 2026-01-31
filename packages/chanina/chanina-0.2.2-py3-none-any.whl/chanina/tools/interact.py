class Interact:
    """ tools for interacting with the page. """
    def __init__(self, session) -> None:
        self.session = session

    def accept_cookies(
        self,
        text: str = "",
        case_sensitive: bool = False,
        recursive: bool = True,
        click_count: int = 1,
        selector: str = "button"
    ) -> None:
        """
        Helper to bypass the "accept cookies" pop ups.
        If no 'text' is specified, then it clicks every buttons that would be a good candidate.
        If text is specified but the buttons is not found an error will be raised.
        If the "text" gets multiple candidates, then they will all be clicked
        unless the "recursive" parameter is changed to False.
    
        Args:
            - text (str): the text that identifies the accept button.
            - case_sensitive (bool): wether or not the search is case sensitive.
            - click_count (int): as those popups appears at dom loading, you might find
                                 cases where clicking multiple times gets the focus correctly.
            - recursive (bool): wether or not we want to click on every candidate buttons.
            - selector (str): Chose in which selectors the button can be found with.
        """
        clicked = False

        buttons = self.session.current_page.locator(selector).all()
        if text:
            buttons = self.session.filters.filter_by_text(buttons, text)

        if not case_sensitive:
            text = text.lower()

        is_btn_candidate = lambda btn_text: text in btn_text if text else (
            "accept" in btn_text
        ) or (
            "allow" in btn_text
        )

        for btn in buttons:
            btn_text = btn.inner_text()
            if not case_sensitive:
                btn_text = btn_text.lower()
            if is_btn_candidate(btn_text):
                btn.click(delay=100, click_count=click_count)
                clicked = True
                if not recursive:
                    break
        if not clicked:
            raise Exception(f"Did not find a cookies button to click.")

    def form_filler(
        self,
        form_data: dict[str, str],
        attribute: str = "id"
    ) -> None:
        """
        Forms are filled by passing a dict.
    
        Args:
            - form_data (dict[str, str]): form fields are a dict
                    with key = *field to fill*, and value is a dict.
            - attribute (str): the HTML attribute identifier. Default to 'id'.
        """
        inputs = self.session.current_page.locator("input").all()
        for field in inputs:
            placeholder = str(field.get_attribute(attribute))
            is_input = form_data.get(placeholder)
            if is_input:
                field.fill(is_input)
                form_data.pop(placeholder)
    
        if form_data.keys():
            raise Exception(
                f"did not find matching '{attribute}' for value(s) {form_data.keys()}."
            )
