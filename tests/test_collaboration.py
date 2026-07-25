"""
Tests for Collaboration & Comments (Prompt 075).
"""
import pytest
from services.collaboration.collaboration_service import CollaborationService
from services.comments.comment_service import CommentService
from services.workspaces.team_workspace_manager import TeamWorkspaceManager, WorkspaceRole


@pytest.fixture
def collab(tmp_path):
    db_twm = tmp_path / "collab_twm.db"
    db_cs = tmp_path / "collab_cs.db"
    db_col = tmp_path / "collab_col.db"

    twm = TeamWorkspaceManager(db_path=str(db_twm))
    cs = CommentService(db_path=str(db_cs), workspace_manager=twm)
    col = CollaborationService(db_path=str(db_col))
    return twm, cs, col


def test_comment_lifecycle(collab):
    twm, cs, col = collab
    twm.create_workspace("ws-team", "Team Beta", "owner1")
    twm.invite_member("ws-team", "owner1", "dev1", WorkspaceRole.DEVELOPER.value)
    twm.invite_member("ws-team", "owner1", "viewer1", WorkspaceRole.VIEWER.value)

    # Developer adds comment
    c_id = cs.add_comment("ws-team", "dev1", "src/App.java", "Fix typo here", line_number=15)
    assert c_id is not None

    # Viewer attempts comment (read-only) -> should be denied
    v_c = cs.add_comment("ws-team", "viewer1", "src/App.java", "Viewer comment")
    assert v_c is None

    # Retrieve comments
    comments = cs.list_comments("ws-team", "src/App.java")
    assert len(comments) == 1
    assert comments[0]["text"] == "Fix typo here"

    # Resolve comment
    assert cs.resolve_comment(c_id, "dev1") is True
    updated = cs.list_comments("ws-team", "src/App.java")
    assert updated[0]["resolved"] is True


def test_saved_searches_and_activity(collab):
    twm, cs, col = collab
    col.save_search("ws-team", "user1", "All Controllers", {"query": "Controller"})
    searches = col.get_saved_searches("ws-team")
    assert len(searches) == 1
    assert searches[0]["name"] == "All Controllers"

    col.record_activity("ws-team", "user1", "QUERY_EXPERT", "Ran analysis")
    feed = col.get_activity_feed("ws-team")
    assert len(feed) == 1
    assert feed[0]["action"] == "QUERY_EXPERT"


def test_presence_tracking(collab):
    twm, cs, col = collab
    col.update_presence("ws-team", "user1")
    active = col.get_active_presence("ws-team")
    assert "user1" in active
