# Patch Release Checklist

This checklist must be followed when releasing a patch version (`x.y.Z`) of ECIP Lite.

## 1. Preparation
- [ ] Create a release branch off `main` (e.g., `release/v1.0.1`).
- [ ] Verify that all regression tests targeting the patch issues are present and passing.
- [ ] Verify that all unit tests and integration tests pass on the release branch.
- [ ] Ensure that no breaking runtime changes or new public-facing APIs are introduced in this patch.

## 2. Documentation Updates
- [ ] Update the project version in `ecip_core/settings.py` or the configuration files.
- [ ] Update `CHANGELOG.md` with:
  - The release version and date.
  - A summary of bug fixes, security patches, and minor enhancements.
  - Contributor credits for PR submitters.

## 3. Release Execution
- [ ] Merge the release branch into `main` via a PR.
- [ ] Tag the merge commit on `main` with the version number (e.g., `git tag -a v1.0.1 -m "Release v1.0.1"`).
- [ ] Push tags to remote (`git push origin v1.0.1`).
- [ ] Build and verify package artifact generation (if publishing to a package manager).

## 4. Post-Release
- [ ] Announce the release in community channels or issue threads.
- [ ] Close related issues that are resolved in the patch.
