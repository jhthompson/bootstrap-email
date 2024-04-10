import os
import unittest
from dataclasses import dataclass
from doctest import Example

import cssutils
from lxml.doctestcompare import LHTMLOutputChecker
from lxml.html import document_fromstring, fragment_fromstring, tostring

from bootstrap_email.compiler import (
    add_missing_meta_tags,
    compile,
    compile_html,
    has_margin_bottom_class,
    has_margin_top_class,
    has_vertical_margin_class,
    inner_html,
    template,
)


def assertHtmlEqual(got: str, want: str):
    checker = LHTMLOutputChecker()
    if not checker.check_output(want, got, 0):
        message = checker.output_difference(Example("", want), got, 0)
        raise AssertionError(message)


def assertHtmlEqualIgnoringStyles(got: str, want: str):
    checker = LHTMLOutputChecker()

    # Parse the HTML strings into lxml elements
    got = document_fromstring(got)
    want = document_fromstring(want)

    # Iterate over the elements in the got and want lxml elements
    for got_el, want_el in zip(got.iter(), want.iter()):
        # If the elements have a style attribute, compare their CSS styles
        if (
            "style" in got_el.attrib
            and "style" in want_el.attrib
            and not are_css_declarations_equal(
                got_el.attrib["style"], want_el.attrib["style"]
            )
        ):
            message = f"CSS styles do not match: {got_el.attrib['style']} != {want_el.attrib['style']}"  # noqa: E501
            raise AssertionError(message)

        # Remove the style attribute from the elements
        got_el.attrib.pop("style", None)
        want_el.attrib.pop("style", None)

    # Compare the got and want lxml elements
    got = tostring(got)
    want = tostring(want)
    if not checker.check_output(want, got, 0):
        message = checker.output_difference(Example("", want), got, 0)
        raise AssertionError(message)


def are_css_declarations_equal(css_1: str, css_2: str) -> bool:
    """Test two CSS declarations for equality, ignoring order of properties.

    Args:
        css_1 (str): First CSS declaration to compare.
        css_2 (str): Second CSS declaration to compare.

    Returns:
        bool: If the two CSS declarations are equal.
    """
    # Parse the CSS strings into CSSStyleDeclaration objects
    css_1_style_declaration = cssutils.parseStyle(css_1)
    css_2_style_declaration = cssutils.parseStyle(css_2)

    # Get the properties and their values from each CSSStyleDeclaration
    css1_dict = {
        prop.name: prop.value
        for prop in css_1_style_declaration.getProperties(all=True)
    }
    css2_dict = {
        prop.name: prop.value
        for prop in css_2_style_declaration.getProperties(all=True)
    }

    # Compare the two dictionaries
    return css1_dict == css2_dict


class AreCssDeclarationsEqualTest(unittest.TestCase):
    def test_are_css_declarations_equal(self):
        css_1 = "color: red; font-size: 8px"
        css_2 = "font-size: 8px; color: red"

        self.assertTrue(are_css_declarations_equal(css_1, css_2))


class AssertHtmlEqualTest(unittest.TestCase):
    def test_assert_html_equal(self):
        with self.assertRaises(AssertionError):
            assertHtmlEqual("<div></div>", "<div></div><p></p>")


class CompileHtmlTest(unittest.TestCase):
    def test_compile_html(self):
        input_dir = "tests/input/integration"
        output_dir = "tests/output/integration"

        for filename in os.listdir(input_dir):
            with (
                self.subTest(filename),
                open(os.path.join(input_dir, filename)) as input_file,
                open(os.path.join(output_dir, filename)) as expected_output_file,
            ):
                html = input_file.read()

                document = compile_html(html)

                assertHtmlEqual(
                    tostring(document, encoding="unicode"), expected_output_file.read()
                )


class ConfigureHtmlTest(unittest.TestCase):
    # TODO: make this use the configure_html() call instead of the individual functions
    #   note: this should be like the above test case where there are input and output
    #   files
    def test_add_missing_meta_tags(self):
        document = document_fromstring("""
        <html>
            <head>
                <meta http-equiv="x-ua-compatible" content="ie=edge">
            </head>
            <body>
            </body>
        </html>
        """)
        add_missing_meta_tags(document)

        expected = """
        <html>
            <head>
                <meta name="x-apple-disable-message-reformatting">
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <meta name="format-detection" content="telephone=no, date=no, address=no, email=no">
                <meta http-equiv="x-ua-compatible" content="ie=edge">
            </head>
            <body>
            </body>
        </html>
        """  # noqa: E501

        assertHtmlEqual(tostring(document, encoding="unicode"), expected)

    def test_template(self):
        template_name = "base.html"
        mapping = {"contents": "<p>Hello, world!</p>"}

        output = template(template_name, mapping)
        expected_output = """
        <html>
            <head>
                <meta content="text/html; charset=utf-8" http-equiv="Content-Type">
                <meta http-equiv="x-ua-compatible" content="ie=edge">
                <meta name="x-apple-disable-message-reformatting">
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <meta name="format-detection" content="telephone=no, date=no, address=no, email=no">
            </head>

            <body>
                <p>Hello, world!</p>
            </body>
        </html>
        """  # noqa: E501

        assertHtmlEqual(output, expected_output)

    def test_has_margin_top_class(self):
        @dataclass
        class TestCase:
            name: str
            input: str
            expected: bool

        test_cases = [
            TestCase(name="mt-5", input='<div class="mt-5"></div>', expected=True),
            TestCase(
                name="mt-lg-5", input='<div class="mt-lg-5"></div>', expected=True
            ),
            TestCase(name="my-5", input='<div class="my-5"></div>', expected=True),
            TestCase(name="mb-5", input='<div class="mb-5"></div>', expected=False),
        ]
        for case in test_cases:
            with self.subTest(case.name):
                got = has_margin_top_class(fragment_fromstring(case.input))
                self.assertEqual(got, case.expected)

    def test_has_margin_bottom_class(self):
        @dataclass
        class TestCase:
            name: str
            input: str
            expected: bool

        test_cases = [
            TestCase(name="mb-5", input='<div class="mb-5"></div>', expected=True),
            TestCase(
                name="mb-lg-5", input='<div class="mb-lg-5"></div>', expected=True
            ),
            TestCase(name="my-5", input='<div class="my-5"></div>', expected=True),
            TestCase(name="mt-5", input='<div class="mt-5"></div>', expected=False),
        ]
        for case in test_cases:
            with self.subTest(case.name):
                got = has_margin_bottom_class(fragment_fromstring(case.input))
                self.assertEqual(got, case.expected)

    def test_has_vertical_margin_class(self):
        @dataclass
        class TestCase:
            name: str
            input: str
            expected: bool

        test_cases = [
            TestCase(
                name="mt-5 mb-5", input='<div class="mt-5 mb-5"></div>', expected=True
            ),
            TestCase(name="mt-5", input='<div class="mt-5"></div>', expected=True),
            TestCase(name="mb-5", input='<div class="mb-5"></div>', expected=True),
            TestCase(name="mx-5", input='<div class="mx-5"></div>', expected=False),
        ]
        for case in test_cases:
            with self.subTest(case.name):
                got = has_vertical_margin_class(fragment_fromstring(case.input))
                self.assertEqual(got, case.expected)

    def test_inner_html(self):
        @dataclass
        class TestCase:
            name: str
            input: str
            expected: bool

        test_cases = [
            TestCase(
                name="div with inner text and p",
                input="<div>In the div <p>in the p</p></div>",
                expected="In the div <p>in the p</p>",
            ),
            TestCase(
                name="div without inner text and p",
                input="<div><p>in the p</p></div>",
                expected="<p>in the p</p>",
            ),
        ]
        for case in test_cases:
            with self.subTest(case.name):
                got = inner_html(fragment_fromstring(case.input))
                self.assertEqual(got, case.expected)


class FinalizeDocumentTest(unittest.TestCase):
    pass


@unittest.skip("Full end-to-end tests are not yet implemented")
class CompileTest(unittest.TestCase):
    def test_compile(self):
        input_dir = "tests/input/end-to-end"
        output_dir = "tests/output/end-to-end"

        for filename in os.listdir(input_dir):
            with (
                self.subTest(filename),
                open(os.path.join(input_dir, filename)) as input_file,
                open(os.path.join(output_dir, filename)) as expected_output_file,
            ):
                html = input_file.read()

                document = compile(html)

                assertHtmlEqualIgnoringStyles(document, expected_output_file.read())


if __name__ == "__main__":
    unittest.main()
