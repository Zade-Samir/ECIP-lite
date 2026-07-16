#!/usr/bin/env python3
import os
import sys

def check_file(path):
    exists = os.path.exists(path)
    if exists:
        print(f"[\033[92mPASS\033[0m] Found: {path}")
        return True
    else:
        print(f"[\033[91mFAIL\033[0m] Missing: {path}")
        return False

def main():
    print("=" * 60)
    print("ECIP Lite Documentation & Maintenance Policy Verification")
    print("=" * 60)

    required_files = [
        "ROADMAP.md",
        "SUPPORT.md",
        "CONTRIBUTING.md",
        ".github/ISSUE_TEMPLATE/bug_report.md",
        ".github/ISSUE_TEMPLATE/feature_request.md",
        ".github/PULL_REQUEST_TEMPLATE.md",
        "docs/maintenance/PATCH_RELEASE_CHECKLIST.md"
    ]

    all_pass = True
    for f in required_files:
        if not check_file(f):
            all_pass = False

    print("=" * 60)
    if all_pass:
        print("\033[92mVerification Successful! All maintenance & governance docs are in place.\033[0m")
        sys.exit(0)
    else:
        print("\033[91mVerification Failed! Some required files are missing.\033[0m")
        sys.exit(1)

if __name__ == "__main__":
    main()
