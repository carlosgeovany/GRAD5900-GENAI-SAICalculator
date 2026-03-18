import unittest

from aidwise.routing import classify_query


class RoutingTests(unittest.TestCase):
    def test_detects_what_if_queries(self) -> None:
        self.assertEqual(classify_query("What if my income decreases?"), "what_if")

    def test_detects_explanation_queries(self) -> None:
        self.assertEqual(classify_query("Why is my Pell low?", has_structured_inputs=True), "explanation")

    def test_defaults_to_information(self) -> None:
        self.assertEqual(classify_query("What is SAI?"), "informational")


if __name__ == "__main__":
    unittest.main()
