import unittest

from app.core.config import Settings
from app.main import create_app

app = create_app(Settings(_env_file=None, environment="test"))


class OpenAPITests(unittest.TestCase):
    def test_contract_has_examples_auth_and_actual_routes(self):
        schema = app.openapi()
        self.assertTrue(schema["info"]["description"])
        self.assertTrue(schema["tags"])
        self.assertTrue(schema["components"]["schemas"]["SiteCreate"]["examples"])
        operation = schema["paths"]["/api/v1/sites"]["post"]
        self.assertTrue(operation["security"])
        self.assertIn("403", operation["responses"])
        self.assertIn("404", operation["responses"])
        self.assertIn("201", operation["responses"])
        self.assertFalse(any("practice" in path for path in schema["paths"]))
