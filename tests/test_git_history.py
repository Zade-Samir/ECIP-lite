import os
import tempfile
import unittest
import shutil
import subprocess
from ecip_core.git.scanner import GitRepositoryScanner


class TestGitHistory(unittest.TestCase):

    def setUp(self):
        self.scanner = GitRepositoryScanner()
        self.temp_dir = tempfile.mkdtemp()
        
        # Initialize a real Git repository in temp_dir for testing
        subprocess.run(["git", "init", "-b", "main"], cwd=self.temp_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        # Configure local git user
        subprocess.run(["git", "config", "user.name", "Test Author"], cwd=self.temp_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=self.temp_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def commit_file(self, filename: str, content: str, message: str):
        filepath = os.path.join(self.temp_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        subprocess.run(["git", "add", filename], cwd=self.temp_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "commit", "-m", message], cwd=self.temp_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def test_git_repo_detection_and_scan(self):
        # 1. Detection
        self.assertTrue(self.scanner.is_git_repo(self.temp_dir))
        
        non_git = os.path.join(self.temp_dir, "nested")
        os.makedirs(non_git)
        self.assertFalse(self.scanner.is_git_repo(non_git))

        # 2. Scan commits
        self.commit_file("File1.java", "public class File1 {}", "Initial commit")
        self.commit_file("File2.java", "public class File2 {}", "Second commit")

        meta = self.scanner.scan(self.temp_dir)
        self.assertNotEqual(meta.head_commit, "unknown")
        self.assertEqual(len(meta.commits), 2)
        
        authors = {c.author for c in meta.commits}
        self.assertIn("Test Author", authors)

    def test_file_history_evolution(self):
        self.commit_file("App.java", "first version", "Create App")
        self.commit_file("App.java", "second version", "Update App")

        file_meta = self.scanner.scan_file_history(self.temp_dir, "App.java")
        self.assertIsNotNone(file_meta)
        self.assertEqual(file_meta.total_revisions, 2)
        self.assertIn("Test Author", file_meta.contributors)
        self.assertNotEqual(file_meta.creation_commit, file_meta.last_modified_commit)


if __name__ == "__main__":
    unittest.main()
