import os
import unittest
import xml.etree.ElementTree as ET


class TestIntelliJPlugin(unittest.TestCase):

    def setUp(self):
        self.plugin_xml_path = "intellij-plugin/src/main/resources/META-INF/plugin.xml"
        self.build_gradle_path = "intellij-plugin/build.gradle.kts"

    def test_plugin_xml_exists_and_is_valid(self):
        self.assertTrue(os.path.exists(self.plugin_xml_path))
        
        # Verify XML structure
        try:
            tree = ET.parse(self.plugin_xml_path)
            root = tree.getroot()
            self.assertEqual(root.tag, "idea-plugin")
            
            # Check plugin name
            name_node = root.find("name")
            self.assertIsNotNone(name_node)
            self.assertEqual(name_node.text, "ECIP Lite")
            
            # Check actions are registered
            actions = root.find("actions")
            self.assertIsNotNone(actions)
            group = actions.find("group")
            self.assertIsNotNone(group)
            self.assertEqual(group.attrib.get("id"), "Ecip.EditorGroup")
            
            actions_list = group.findall("action")
            self.assertGreaterEqual(len(actions_list), 5)
            
            # Verify specific actions exist
            action_ids = [a.attrib.get("id") for a in actions_list]
            self.assertIn("Ecip.AskQuestion", action_ids)
            self.assertIn("Ecip.ExplainSelection", action_ids)
            self.assertIn("Ecip.ShowDependencies", action_ids)
            
        except Exception as e:
            self.fail(f"plugin.xml parsing failed: {e}")

    def test_build_gradle_config(self):
        self.assertTrue(os.path.exists(self.build_gradle_path))
        with open(self.build_gradle_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("group = \"com.samirzade.ecip\"", content)
        self.assertIn("org.jetbrains.intellij", content)


if __name__ == "__main__":
    unittest.main()
