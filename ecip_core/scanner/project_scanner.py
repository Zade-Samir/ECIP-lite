from pathlib import Path


class ProjectScanner:
    """
    Scans a project and returns all Java source files.
    """

    def scan(self, project_path: str) -> list[Path]:

        project = Path(project_path)

        return list(project.rglob("*.java"))