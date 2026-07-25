"""
Tests for JobRegistry and JobHistory (Prompt 067).
"""
import time
import pytest
from services.scheduler.job_registry import JobRegistry
from services.scheduler.job_history import JobHistory, JobStatus


class TestJobRegistry:
    def test_register_and_get(self):
        reg = JobRegistry()
        fn = lambda: None
        reg.register("my_job", fn)
        assert reg.get("my_job") is fn

    def test_get_unregistered_returns_none(self):
        reg = JobRegistry()
        assert reg.get("nonexistent") is None

    def test_list_jobs(self):
        reg = JobRegistry()
        reg.register("job_a", lambda: None)
        reg.register("job_b", lambda: None)
        names = [j["name"] for j in reg.list_jobs()]
        assert "job_a" in names
        assert "job_b" in names

    def test_is_registered(self):
        reg = JobRegistry()
        reg.register("present", lambda: None)
        assert reg.is_registered("present") is True
        assert reg.is_registered("absent") is False

    def test_unregister(self):
        reg = JobRegistry()
        reg.register("to_remove", lambda: None)
        result = reg.unregister("to_remove")
        assert result is True
        assert reg.get("to_remove") is None

    def test_unregister_nonexistent_returns_false(self):
        reg = JobRegistry()
        assert reg.unregister("ghost") is False


class TestJobHistory:
    @pytest.fixture
    def history(self, tmp_path):
        return JobHistory(db_path=str(tmp_path / "test_hist.db"))

    def test_record_and_retrieve_success(self, history):
        history.record_start("exec1", "job1", "TestJob")
        history.record_success("exec1")
        records = history.get_history(job_id="job1")
        assert len(records) == 1
        assert records[0]["status"] == JobStatus.SUCCESS

    def test_record_and_retrieve_failure(self, history):
        history.record_start("exec2", "job2", "FailJob")
        history.record_failure("exec2", "Something went wrong")
        records = history.get_history(job_id="job2")
        assert records[0]["status"] == JobStatus.FAILED
        assert "Something went wrong" in records[0]["error"]

    def test_get_all_history(self, history):
        history.record_start("e1", "j1", "A")
        history.record_success("e1")
        history.record_start("e2", "j2", "B")
        history.record_failure("e2", "err")
        all_records = history.get_history()
        assert len(all_records) == 2

    def test_stats(self, history):
        history.record_start("s1", "j1", "A")
        history.record_success("s1")
        history.record_start("s2", "j2", "B")
        history.record_failure("s2", "err")
        stats = history.get_stats()
        assert stats["total"] == 2
        assert stats["success"] == 1
        assert stats["failed"] == 1

    def test_limit(self, history):
        for i in range(10):
            history.record_start(f"e{i}", "j1", "bulk")
            history.record_success(f"e{i}")
        records = history.get_history(limit=5)
        assert len(records) == 5
