"""
Tests for Production Release Validation (Prompt 100).
"""
import pytest
from scripts.release.build_release import ReleasePackager


def test_v1_release_packaging():
    packager = ReleasePackager()
    res = packager.validate_and_package("1.0.0", 100)

    assert res["status"] == "RELEASED"
    assert res["version"] == "1.0.0"
    assert res["subsystems_verified"] == 100
    assert res["is_signed"] is True
