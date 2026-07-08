import unittest
from ecip_core.query.entity_extractor import EntityExtractor
from ecip_core.query.models.entity_result import EntityResult


class TestEntityExtractor(unittest.TestCase):

    def setUp(self):
        self.extractor = EntityExtractor()

    def test_class_extractions(self):
        results = self.extractor.extract_entities("Explain UserService")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].entity_type, "service_name")
        self.assertEqual(results[0].entity_name, "UserService")
        self.assertEqual(results[0].confidence, 1.0)

        results = self.extractor.extract_entities("Explain BookingController")
        self.assertEqual(results[0].entity_type, "controller_name")

        results = self.extractor.extract_entities("Explain UserRepository")
        self.assertEqual(results[0].entity_type, "repository_name")

        results = self.extractor.extract_entities("Explain UserDTO")
        self.assertEqual(results[0].entity_type, "entity_name")

        results = self.extractor.extract_entities("Explain Customer")
        self.assertEqual(results[0].entity_type, "class_name")
        self.assertEqual(results[0].confidence, 0.9)

    def test_method_extractions(self):
        results = self.extractor.extract_entities("Where is getUserById implemented?")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].entity_type, "method_name")
        self.assertEqual(results[0].entity_name, "getUserById")
        self.assertEqual(results[0].confidence, 0.8)

        results_explicit = self.extractor.extract_entities("Show method saveUser details")
        self.assertEqual(len(results_explicit), 1)
        self.assertEqual(results_explicit[0].entity_name, "saveUser")
        self.assertEqual(results_explicit[0].confidence, 1.0)
        self.assertEqual(results_explicit[0].matched_text, "method saveUser")

    def test_package_extraction(self):
        results = self.extractor.extract_entities("Search package com.example.auth.service details")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].entity_type, "package_name")
        self.assertEqual(results[0].entity_name, "com.example.auth.service")
        self.assertEqual(results[0].confidence, 1.0)

    def test_rest_endpoint_extraction(self):
        results = self.extractor.extract_entities("Show GET mapping for /api/v1/bookings/{id}")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].entity_type, "rest_endpoint")
        self.assertEqual(results[0].entity_name, "/api/v1/bookings/{id}")
        self.assertEqual(results[0].confidence, 1.0)

    def test_multiple_entities_preserves_order(self):
        query = "Explain UserService, UserRepository, and method register"
        results = self.extractor.extract_entities(query)
        self.assertEqual(len(results), 3)

        self.assertEqual(results[0].entity_name, "UserService")
        self.assertEqual(results[0].entity_type, "service_name")

        self.assertEqual(results[1].entity_name, "UserRepository")
        self.assertEqual(results[1].entity_type, "repository_name")

        self.assertEqual(results[2].entity_name, "register")
        self.assertEqual(results[2].entity_type, "method_name")

    def test_empty_and_unknown_queries(self):
        self.assertEqual(self.extractor.extract_entities(""), [])
        self.assertEqual(self.extractor.extract_entities("   "), [])
        self.assertEqual(self.extractor.extract_entities("explain show list where what"), [])

    def test_ambiguous_entity_warning_logged(self):
        with self.assertLogs("ecip_core.query.entity_extractor", level="WARNING") as log_capture:
            results = self.extractor.extract_entities("Show getUserById details")
            self.assertEqual(len(results), 1)
            self.assertTrue(any("Ambiguous entity" in log for log in log_capture.output))

    def test_backward_compatibility_class_and_method(self):
        self.assertEqual(self.extractor.extract_class_name("Explain UserService"), "UserService")
        self.assertEqual(self.extractor.extract_method_name("Explain getUserById"), "getUserById")
        self.assertIsNone(self.extractor.extract_class_name("no entities here"))
        self.assertIsNone(self.extractor.extract_method_name("no entities here"))

    def test_serialization(self):
        res = EntityResult(
            entity_type="service_name",
            entity_name="UserService",
            confidence=1.0,
            matched_text="UserService",
            normalized_value="userservice"
        )
        serialized = res.model_dump()
        self.assertEqual(serialized["entity_type"], "service_name")
        self.assertEqual(serialized["entity_name"], "UserService")


if __name__ == "__main__":
    unittest.main()
