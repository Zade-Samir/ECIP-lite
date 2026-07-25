"""
Tests for Team Workspaces (Prompt 075).
"""
import pytest
from services.workspaces.team_workspace_manager import TeamWorkspaceManager, WorkspaceRole


@pytest.fixture
def twm(tmp_path):
    db_file = tmp_path / "test_twm.db"
    return TeamWorkspaceManager(db_path=str(db_file))


def test_create_workspace(twm):
    assert twm.create_workspace("ws-1", "Team Alpha", "alice") is True
    assert twm.get_role("ws-1", "alice") == WorkspaceRole.OWNER.value


def test_invite_member(twm):
    twm.create_workspace("ws-1", "Team Alpha", "alice")

    # Owner invites bob as developer
    assert twm.invite_member("ws-1", "alice", "bob", WorkspaceRole.DEVELOPER.value) is True
    assert twm.get_role("ws-1", "bob") == WorkspaceRole.DEVELOPER.value

    # Duplicate invitation returns False
    assert twm.invite_member("ws-1", "alice", "bob") is False

    # Member without permission tries to invite charlie
    assert twm.invite_member("ws-1", "bob", "charlie") is False


def test_transfer_ownership(twm):
    twm.create_workspace("ws-1", "Team Alpha", "alice")
    twm.invite_member("ws-1", "alice", "bob", WorkspaceRole.DEVELOPER.value)

    assert twm.transfer_ownership("ws-1", "alice", "bob") is True
    assert twm.get_role("ws-1", "bob") == WorkspaceRole.OWNER.value
    assert twm.get_role("ws-1", "alice") == WorkspaceRole.ADMIN.value
