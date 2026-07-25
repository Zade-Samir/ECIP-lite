import os
import tempfile
import unittest
import shutil
from ecip_core.parser.config.config_parser import ConfigParser


class TestConfigParser(unittest.TestCase):

    def setUp(self):
        self.parser = ConfigParser()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def write_config_file(self, filename: str, content: str) -> str:
        filepath = os.path.join(self.temp_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return filepath

    def test_properties_parsing(self):
        content = """
        # Database setup
        spring.datasource.url=jdbc:mysql://localhost:3306/mydb
        spring.profiles.active=dev,test
        server.port=8080
        custom.property = hello-world
        """
        filepath = self.write_config_file("application.properties", content)
        meta = self.parser.parse(filepath)

        self.assertEqual(meta.server_port, "8080")
        self.assertEqual(meta.datasource_url, "jdbc:mysql://localhost:3306/mydb")
        self.assertEqual(meta.profiles, ["dev", "test"])
        self.assertEqual(meta.properties.get("custom.property"), "hello-world")

    def test_yaml_parsing(self):
        content = """
        spring:
          profiles:
            active: prod
          datasource:
            url: jdbc:postgresql://localhost:5432/proddb
        server:
          port: 9090
        """
        filepath = self.write_config_file("application.yml", content)
        meta = self.parser.parse(filepath)

        self.assertEqual(meta.server_port, "9090")
        self.assertEqual(meta.datasource_url, "jdbc:postgresql://localhost:5432/proddb")
        self.assertEqual(meta.profiles, ["prod"])
        self.assertEqual(meta.properties.get("spring.profiles.active"), "prod")

    def test_empty_config(self):
        filepath = self.write_config_file("empty.properties", "")
        meta = self.parser.parse(filepath)
        self.assertEqual(len(meta.properties), 0)


if __name__ == "__main__":
    unittest.main()
