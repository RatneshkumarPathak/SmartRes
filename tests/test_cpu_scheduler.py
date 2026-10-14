
from core.cpu_scheduler import fcfs, round_robin


def test_fcfs_metrics():
    processes = [
        {"pid": "P1", "arrival": 0, "burst": 5},
        {"pid": "P2", "arrival": 1, "burst": 3},
        {"pid": "P3", "arrival": 2, "burst": 1},
    ]

    results, timeline = fcfs(processes)

    assert [p["completion"] for p in results] == [5, 8, 9]
    assert [p["waiting"] for p in results] == [0, 4, 6]
    assert len(timeline) == 3


def test_round_robin_metrics():
    processes = [
        {"pid": "P1", "arrival": 0, "burst": 5},
        {"pid": "P2", "arrival": 1, "burst": 3},
        {"pid": "P3", "arrival": 2, "burst": 1},
    ]

    results, timeline = round_robin(processes, 2)

    assert [p["completion"] for p in results] == [9, 8, 5]
    assert [p["waiting"] for p in results] == [4, 4, 2]
    assert sum(p["burst"] for p in results) == sum(
        event["finish"] - event["start"] for event in timeline
    )


def test_round_robin_rejects_invalid_quantum():
    processes = [{"pid": "P1", "arrival": 0, "burst": 4}]

    try:
        round_robin(processes, 0)
        assert False, "Expected ValueError"
    except ValueError:
        pass


def test_fcfs_handles_idle_time():
    processes = [
        {"pid": "P1", "arrival": 3, "burst": 2},
    ]

    results, timeline = fcfs(processes)

    assert results[0]["start"] == 3
    assert results[0]["completion"] == 5
    assert timeline[0]["start"] == 3
