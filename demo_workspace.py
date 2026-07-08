import os
import sys
import shutil
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.absolute()))

from ecip_core.workspace.manager import workspace_manager
from ecip_core.storage.sqlite.database import Database
from ecip_core.storage.sqlite.repository import JavaRepository
from ecip_core.parser.models.parsed_java_file import ParsedJavaFile


def run_demo():
    print("======================================================================")
    print("⚡ Starting ECIP Lite Multi-Project Workspace Management Demo")
    print("======================================================================\n")

    # Step 1: Clean any existing test workspaces
    print("1. Cleaning up previous project workspaces...")
    workspace_manager.delete_workspace("proj_a")
    workspace_manager.delete_workspace("proj_b")
    print("   Clean complete.")

    # Step 2: Register two workspaces
    print("\n2. Registering two isolated workspaces:")
    res_a = workspace_manager.register_workspace(
        project_id="proj_a",
        alias="Spring Boot Project A",
        root_path="projects/spring-boot-a"
    )
    print(f"   Registered Workspace A: {res_a['alias']} (id={res_a['project_id']})")

    res_b = workspace_manager.register_workspace(
        project_id="proj_b",
        alias="Spring Boot Project B",
        root_path="projects/spring-boot-b"
    )
    print(f"   Registered Workspace B: {res_b['alias']} (id={res_b['project_id']})")

    # Step 3: Index/Save file metadata to Project A
    print("\n3. Activating Project A and saving ClassA.java metadata...")
    workspace_manager.set_active_workspace("proj_a")
    
    repo = JavaRepository()
    file_a = ParsedJavaFile(
        file_name="ClassA.java",
        file_path="projects/spring-boot-a/ClassA.java",
        package_name="com.example.a",
        class_name="ClassA",
        methods=[]
    )
    repo.save(file_a, file_hash="hash_class_a")
    print(f"   Saved ClassA in active project: {workspace_manager.get_active_workspace()}")

    # Step 4: Verify Project B remains isolated and empty
    print("\n4. Switching to Project B and verifying workspace is empty...")
    workspace_manager.set_active_workspace("proj_b")
    print(f"   Active project switched to: {workspace_manager.get_active_workspace()}")
    
    files_in_b = repo.get_all_files()
    print(f"   Files found in Project B: {len(files_in_b)}")
    if len(files_in_b) == 0:
        print("   ✅ SUCCESS: Project B has zero metadata (Perfect isolation!).")

    # Step 5: Save file metadata to Project B
    print("\n5. Saving ClassB.java metadata in Project B...")
    file_b = ParsedJavaFile(
        file_name="ClassB.java",
        file_path="projects/spring-boot-b/ClassB.java",
        package_name="com.example.b",
        class_name="ClassB",
        methods=[]
    )
    repo.save(file_b, file_hash="hash_class_b")
    print(f"   Saved ClassB in active project: {workspace_manager.get_active_workspace()}")

    # Step 6: Verify file lists are completely isolated
    print("\n6. Verifying isolated file list records:")
    files_in_b = repo.get_all_files()
    print(f"   Files in Project B: {[f['class_name'] for f in files_in_b]}")

    workspace_manager.set_active_workspace("proj_a")
    files_in_a = repo.get_all_files()
    print(f"   Files in Project A: {[f['class_name'] for f in files_in_a]}")

    # Check isolation correctness
    assert len(files_in_a) == 1 and files_in_a[0]["class_name"] == "ClassA"
    assert len(files_in_b) == 1 and files_in_b[0]["class_name"] == "ClassB"
    print("   ✅ SUCCESS: Dynamic database routing works 100% correctly!")

    # Step 7: Print workspace stats
    print("\n7. Extracting workspace statistics:")
    stats_a = workspace_manager.get_workspace_stats("proj_a")
    stats_b = workspace_manager.get_workspace_stats("proj_b")
    print(f"   Stats Project A: {stats_a}")
    print(f"   Stats Project B: {stats_b}")

    # Step 8: Deletion verification
    print("\n8. Deleting Project A and verifying file unlinking...")
    workspace_manager.set_active_workspace("default")
    workspace_manager.delete_workspace("proj_a")
    
    db_file_a = Path("data/ecip_proj_a.db")
    print(f"   Project A database file exists: {db_file_a.exists()}")
    if not db_file_a.exists():
        print("   ✅ SUCCESS: Workspace database unlinked successfully!")

    print("\n======================================================================")
    print("🎉 Workspace Demo complete! Multi-Project Workspace verified successfully.")
    print("======================================================================")


if __name__ == "__main__":
    run_demo()
