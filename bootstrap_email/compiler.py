from bs4 import BeautifulSoup


class Compiler:
    def __init__(self, html):
        self.document = BeautifulSoup(html, "html.parser")

    def compile(self) -> str:
        # TODO: Implement this method
        return ""
