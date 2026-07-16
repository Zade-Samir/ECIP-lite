# Support Policy

Thank you for using ECIP Lite! This document outlines how to get help, report bugs, request features, and our policy on supporting older versions.

## Getting Help

Before opening a new issue, please check the following resources:
- **Documentation:** Review [README.md](file:///Users/samirzade/Codes/ecip-lite/README.md) and the contents of the `/docs` directory.
- **Existing Issues:** Search the GitHub Issues page to see if your question or problem has already been addressed.

## Creating an Issue

If you need to report a bug or request a feature, please use the appropriate GitHub issue template:
- **Bug Reports:** Provide a clear description, reproduction steps, system details, and log outputs.
- **Feature Requests:** Outline the use case, desired behavior, and potential implementation ideas.

---

## Support Cadence

We support ECIP Lite versions as follows:

| Version | Release Date | Support Status | End of Support |
| :--- | :--- | :--- | :--- |
| **v1.0.x** | July 2026 | Active (LTS) | July 2027 |
| **v0.9.x** | Pre-release | Deprecated | Immediate |

- **Active Support (LTS):** Active versions receive security patches, critical bug fixes, and compatibility updates.
- **Deprecated:** Older minor versions do not receive updates. Users are strongly encouraged to upgrade to the latest stable version.

---

## Deprecation Policy

When a feature or API is planned for removal, we adhere to the following deprecation cycle:
1. **Notice (Minor Release):** The feature is marked as deprecated in the codebase and documentation. A compiler/runtime warning is added if applicable.
2. **Removal (Next Major Release):** The deprecated feature is completely removed. Migration instructions will be provided in the release notes.
