"""Static guard for Webots template delimiters touching VRML identifiers.

This checks the reported lexical bug; it is not a Webots parser substitute.
"""
from pathlib import Path
import re
import unittest


class ProtoSyntax(unittest.TestCase):
    def test_template_expressions_have_token_boundaries(self):
        source = (Path(__file__).resolve().parents[1] / 'protos/IndoorBot.proto').read_text()
        self.assertIsNone(re.search(r'[A-Za-z0-9_]%<=|>%[A-Za-z0-9_]', source),
                          'Emit a complete identifier inside the template expression')


if __name__ == '__main__':
    unittest.main()
