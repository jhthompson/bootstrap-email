from importlib.resources import files
import unittest

from bootstrap_email.compiler import Compiler


class TestCompile(unittest.TestCase):
    def test_combinations(self):
        cases = [
            "images",
            "integration",
            "lyft",
            "number-test",
            "product-hunt",
        ]

        for case in cases:
            with self.subTest(case):
                input_fixture = (
                    files("tests")
                    .joinpath(f"input/combinations/{case}.html")
                    .read_text()
                )
                output_fixture = (
                    files("tests")
                    .joinpath(f"output/combinations/{case}.html")
                    .read_text()
                )

                compiler = Compiler(input_fixture)
                output = compiler.compile()

                self.assertEqual(output, output_fixture)

    def test_components(self):
        cases = [
            "alert",
            "badge",
            "button",
            "card",
            "container-fluid",
            "container",
            "grid",
            "hr",
            "preview",
            "stack",
            "table",
        ]

        for case in cases:
            with self.subTest(case):
                input_fixture = (
                    files("tests").joinpath(f"input/components/{case}.html").read_text()
                )
                output_fixture = (
                    files("tests")
                    .joinpath(f"output/components/{case}.html")
                    .read_text()
                )

                compiler = Compiler(input_fixture)
                output = compiler.compile()

                self.assertEqual(output, output_fixture)

    def test_utilities(self):
        cases = [
            "align",
            "background",
            "border-radius",
            "color",
            "display",
            "sizing",
            "spacing",
            "to-table",
            "typography",
            "vertical-align",
        ]

        for case in cases:
            with self.subTest(case):
                input_fixture = (
                    files("tests").joinpath(f"input/utilities/{case}.html").read_text()
                )
                output_fixture = (
                    files("tests").joinpath(f"output/utilities/{case}.html").read_text()
                )

                compiler = Compiler(input_fixture)
                output = compiler.compile()

                self.assertEqual(output, output_fixture)
