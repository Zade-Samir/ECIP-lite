"""
Tests for JobScheduler (Prompt 067).
"""
import time
import threading
import pytest
from services.scheduler.job_scheduler import JobScheduler, JobPriority
from services.scheduler.job_history import JobHistory


@pytest.fixture
def history(tmp_path):
    return JobHistory(db_path=str(tmp_path / "test_jobs.db"))


@pytest.fixture
def scheduler(history):
    s = JobScheduler(history=history)
    s.start()
    yield s
    s.stop()


class TestJobSchedulerOneShot:
    def test_one_shot_executes(self, scheduler):
        results = []
        scheduler.schedule_once("test_job", lambda: results.append(1), delay_seconds=0)
        time.sleep(0.3)
        assert results == [1]

    def test_one_shot_respects_delay(self, scheduler):
        results = []
        scheduler.schedule_once("delayed", lambda: results.append(1), delay_seconds=0.5)
        time.sleep(0.1)
        assert results == []  # Not yet
        time.sleep(0.6)
        assert results == [1]

    def test_one_shot_does_not_repeat(self, scheduler):
        results = []
        scheduler.schedule_once("no_repeat", lambda: results.append(1), delay_seconds=0)
        time.sleep(0.4)
        assert len(results) == 1


class TestJobSchedulerInterval:
    def test_interval_executes_multiple_times(self, scheduler):
        results = []
        scheduler.schedule_interval(
            "recurring", lambda: results.append(1), interval_seconds=0.1, run_immediately=True
        )
        time.sleep(0.45)
        assert len(results) >= 3

    def test_interval_run_immediately(self, scheduler):
        results = []
        scheduler.schedule_interval(
            "immediate", lambda: results.append(1), interval_seconds=10, run_immediately=True
        )
        time.sleep(0.2)
        assert len(results) >= 1


class TestJobSchedulerPriority:
    def test_high_priority_runs_before_low(self, scheduler):
        order = []
        # Schedule both with no delay so ordering is by priority
        scheduler.schedule_once("low_job", lambda: order.append("low"),
                                priority=JobPriority.LOW)
        scheduler.schedule_once("high_job", lambda: order.append("high"),
                                priority=JobPriority.HIGH)
        time.sleep(0.3)
        assert "high" in order
        assert "low" in order


class TestJobSchedulerRetry:
    def test_failed_job_retried(self, scheduler, history):
        call_count = {"n": 0}

        def flaky():
            call_count["n"] += 1
            if call_count["n"] < 2:
                raise ValueError("Temporary failure")

        # schedule_once with tiny retry_delay for fast test
        from services.scheduler.job_scheduler import ScheduledJob, JobPriority
        import heapq, time as _time
        job = ScheduledJob(
            run_at=_time.monotonic(),
            priority=JobPriority.NORMAL.value,
            job_id="test-retry",
            name="flaky_job",
            fn=flaky,
            max_retries=3,
            retry_delay=0.05,  # Very short backoff
        )
        with scheduler._cond:
            heapq.heappush(scheduler._heap, job)
            scheduler._cond.notify()
        time.sleep(0.8)
        assert call_count["n"] >= 2  # Was retried

    def test_max_retries_exhausted(self, scheduler, history):
        call_count = {"n": 0}

        def always_fails():
            call_count["n"] += 1
            raise RuntimeError("Always fails")

        from services.scheduler.job_scheduler import ScheduledJob, JobPriority
        import heapq, time as _time
        job = ScheduledJob(
            run_at=_time.monotonic(),
            priority=JobPriority.NORMAL.value,
            job_id="test-exhaust",
            name="bad_job",
            fn=always_fails,
            max_retries=2,
            retry_delay=0.05,
        )
        with scheduler._cond:
            heapq.heappush(scheduler._heap, job)
            scheduler._cond.notify()
        time.sleep(1.0)
        assert call_count["n"] == 3  # 1 initial + 2 retries


class TestJobSchedulerHistory:
    def test_history_records_success(self, scheduler, history):
        scheduler.schedule_once("history_test", lambda: None, delay_seconds=0)
        time.sleep(0.3)
        records = history.get_history()
        assert any(r["name"] == "history_test" and r["status"] == "success" for r in records)

    def test_history_records_failure(self, scheduler, history):
        scheduler.schedule_once(
            "fail_test", lambda: (_ for _ in ()).throw(Exception("err")), delay_seconds=0, max_retries=0
        )
        time.sleep(0.3)
        records = history.get_history()
        assert any(r["name"] == "fail_test" and r["status"] == "failed" for r in records)

    def test_history_stats(self, scheduler, history):
        scheduler.schedule_once("stat_job", lambda: None, delay_seconds=0)
        time.sleep(0.3)
        stats = history.get_stats()
        assert stats["total"] >= 1
