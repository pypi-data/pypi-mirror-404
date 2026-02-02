import unittest
import json
import os
from omicsguard.validator import validate_metadata, ValidationError, MetadataValidator
from omicsguard.loader import SchemaLoader

class TestOmicsGuard(unittest.TestCase):
    def setUp(self):
        self.test_dir = os.path.dirname(os.path.abspath(__file__))
        self.schema_path = os.path.join(self.test_dir, 'data', 'schema.json')
        self.valid_data_path = os.path.join(self.test_dir, 'data', 'valid.json')
        self.invalid_data_path = os.path.join(self.test_dir, 'data', 'invalid.json')

        with open(self.schema_path) as f:
            self.schema = json.load(f)
        with open(self.valid_data_path) as f:
            self.valid_data = json.load(f)
        with open(self.invalid_data_path) as f:
            self.invalid_data = json.load(f)

    def test_validation_success(self):
        errors = validate_metadata(self.valid_data, self.schema)
        self.assertEqual(len(errors), 0)

    def test_validation_failure(self):
        errors = validate_metadata(self.invalid_data, self.schema)
        self.assertGreater(len(errors), 0)
        # Check for specific error messages (updated for new invalid.json)
        messages = [e.message for e in errors]
        # Expecting failure on Enum for sex and Type string for id
        self.assertTrue(any("is not one of" in m for m in messages) or any("is not of type" in m for m in messages))

    def test_loader_local(self):
        loader = SchemaLoader()
        schema = loader.load_schema(self.schema_path)
        self.assertIsInstance(schema, dict)
        self.assertEqual(schema['properties']['id']['type'], 'string')

    def test_plugin_validation(self):
        # Create a dummy plugin function
        def dummy_plugin(data):
            if "bad_field" in data:
                return ["Found bad field"]
            return []
        
        validator = MetadataValidator(schema_dict=self.schema)
        # Manually register the plugin function for testing without file loading
        validator.plugin_functions = [dummy_plugin]
        
        data = self.valid_data.copy()
        data["bad_field"] = True
        
        errors = validator.validate(data)
        self.assertTrue(any("Found bad field" in e.message for e in errors))

if __name__ == '__main__':
    unittest.main()
