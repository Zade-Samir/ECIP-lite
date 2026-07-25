import unittest
import os
import tempfile
import shutil
from pathlib import Path

from ecip_core.parser.java.java_parser import JavaParser
from ecip_core.callgraph.builder import CallGraphBuilder
from ecip_core.storage.sqlite.database import Database
from ecip_core.workspace.manager import workspace_manager


class TestCallGraph(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.parser = JavaParser()
        self.builder = CallGraphBuilder()

        # Clean projects table for test-run isolation
        conn = Database.get_registry_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM projects WHERE project_id = 'test_cg'")
        conn.commit()

        # Register and set active workspace
        workspace_manager.register_workspace("test_cg", "Test CG", self.temp_dir)
        workspace_manager.set_active_workspace("test_cg")

    def tearDown(self):
        workspace_manager.delete_workspace("test_cg")
        shutil.rmtree(self.temp_dir)

    def write_temp_file(self, filename: str, content: str) -> str:
        filepath = Path(self.temp_dir) / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return str(filepath)

    def test_local_recursive_and_cross_class_calls(self):
        class_a_content = """
        package com.example;
        public class ClassA {
            private ClassB serviceB;
            
            public void method1() {
                serviceB.doSomething();
                localMethod();
            }
            
            public void localMethod() {
                localMethod();
            }
        }
        """
        class_b_content = """
        package com.example;
        public class ClassB {
            public void doSomething() {
                System.out.println("Hello");
            }
        }
        """

        file_a = self.write_temp_file("ClassA.java", class_a_content)
        file_b = self.write_temp_file("ClassB.java", class_b_content)

        parsed_a = self.parser.parse(file_a)
        parsed_b = self.parser.parse(file_b)

        self.builder.build("test_cg", [parsed_a, parsed_b])

        outgoing_a_m1 = self.builder.get_outgoing_calls("test_cg", "ClassA.method1")
        self.assertEqual(len(outgoing_a_m1), 2)
        
        targets_from_m1 = [r["target_method"] for r in outgoing_a_m1]
        self.assertIn("ClassB.doSomething", targets_from_m1)
        self.assertIn("ClassA.localMethod", targets_from_m1)

        outgoing_local = self.builder.get_outgoing_calls("test_cg", "ClassA.localMethod")
        self.assertEqual(len(outgoing_local), 1)
        self.assertEqual(outgoing_local[0]["target_method"], "ClassA.localMethod")

    def test_incremental_updates_and_duplicate_prevention(self):
        class_a_content_1 = """
        public class ClassA {
            private ClassB service;
            public void run() {
                service.execute();
            }
        }
        """
        class_b_content = """
        public class ClassB {
            public void execute() {}
        }
        """
        file_a = self.write_temp_file("ClassA.java", class_a_content_1)
        file_b = self.write_temp_file("ClassB.java", class_b_content)

        parsed_a_1 = self.parser.parse(file_a)
        parsed_b = self.parser.parse(file_b)

        self.builder.build("test_cg", [parsed_a_1, parsed_b])

        outgoing = self.builder.get_outgoing_calls("test_cg", "ClassA.run")
        self.assertEqual(len(outgoing), 1)
        self.assertEqual(outgoing[0]["target_method"], "ClassB.execute")

        class_a_content_2 = """
        public class ClassA {
            public void run() {
                localMethod();
            }
            public void localMethod() {}
        }
        """
        self.write_temp_file("ClassA.java", class_a_content_2)
        parsed_a_2 = self.parser.parse(file_a)

        self.builder.build("test_cg", [parsed_a_2, parsed_b])

        outgoing_updated = self.builder.get_outgoing_calls("test_cg", "ClassA.run")
        self.assertEqual(len(outgoing_updated), 1)
        self.assertEqual(outgoing_updated[0]["target_method"], "ClassA.localMethod")


if __name__ == "__main__":
    unittest.main()
