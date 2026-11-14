import pytest

from core.cpu_scheduler import (
    fcfs,
    preemptive_priority,
    priority_scheduling,
    round_robin,
    sjf,
    srtf,
)


SAMPLE = [
    {"pid": "P1", "arrival": 0, "burst": 5},
    {"pid": "P2", "arrival": 1, "burst": 3},
    {"pid": "P3", "arrival": 2, "burst": 1},
]


def test_fcfs_metrics():
    results, timeline = fcfs(SAMPLE)
    assert [p["completion"] for p in results] == [5, 8, 9]
    assert [p["waiting"] for p in results] == [0, 4, 6]
    assert len(timeline) == 3


def test_round_robin_metrics():
    results, timeline = round_robin(SAMPLE, 2)
    assert [p["completion"] for p in results] == [9, 8, 5]
    assert [p["waiting"] for p in results] == [4, 4, 2]
    assert sum(p["burst"] for p in results) == sum(
        event["finish"] - event["start"] for event in timeline
    )


def test_round_robin_rejects_invalid_quantum():
    with pytest.raises(ValueError):
        round_robin([{"pid": "P1", "arrival": 0, "burst": 4}], 0)


def test_fcfs_handles_idle_time():
    results, timeline = fcfs([{"pid": "P1", "arrival": 3, "burst": 2}])
    assert results[0]["start"] == 3
    assert results[0]["completion"] == 5
    assert timeline[0]["start"] == 3


def test_sjf_selects_shortest_ready_job():
    processes = [
        {"pid": "P1", "arrival": 0, "burst": 7},
        {"pid": "P2", "arrival": 2, "burst": 2},
        {"pid": "P3", "arrival": 2, "burst": 1},
    ]
    results, timeline = sjf(processes)
    assert [event["pid"] for event in timeline] == ["P1", "P3", "P2"]
    assert {p["pid"]: p["completion"] for p in results} == {
        "P1": 7, "P2": 10, "P3": 8
    }


def test_srtf_preempts_when_shorter_job_arrives():
    processes = [
        {"pid": "P1", "arrival": 0, "burst": 8},
        {"pid": "P2", "arrival": 1, "burst": 2},
    ]
    results, timeline = srtf(processes)
    assert timeline == [
        {"pid": "P1", "start": 0, "finish": 1},
        {"pid": "P2", "start": 1, "finish": 3},
        {"pid": "P1", "start": 3, "finish": 10},
    ]
    assert {p["pid"]: p["waiting"] for p in results} == {"P1": 2, "P2": 0}


def test_priority_non_preemptive_uses_smaller_number_first():
    processes = [
        {"pid": "P1", "arrival": 0, "burst": 4, "priority": 3},
        {"pid": "P2", "arrival": 1, "burst": 2, "priority": 1},
        {"pid": "P3", "arrival": 1, "burst": 1, "priority": 2},
    ]
    _, timeline = priority_scheduling(processes)
    assert [event["pid"] for event in timeline] == ["P1", "P2", "P3"]


def test_preemptive_priority_preempts_for_higher_priority():
    processes = [
        {"pid": "P1", "arrival": 0, "burst": 5, "priority": 3},
        {"pid": "P2", "arrival": 2, "burst": 2, "priority": 1},
    ]
    _, timeline = preemptive_priority(processes)
    assert timeline == [
        {"pid": "P1", "start": 0, "finish": 2},
        {"pid": "P2", "start": 2, "finish": 4},
        {"pid": "P1", "start": 4, "finish": 7},
    ]


def test_priority_defaults_to_zero_for_old_callers():
    results, _ = priority_scheduling([
        {"pid": "P1", "arrival": 0, "burst": 2},
        {"pid": "P2", "arrival": 0, "burst": 1},
    ])
    assert all(p["priority"] == 0 for p in results)


def test_all_algorithms_preserve_cpu_work():
    algorithms = [
        lambda: fcfs(SAMPLE),
        lambda: sjf(SAMPLE),
        lambda: srtf(SAMPLE),
        lambda: priority_scheduling(SAMPLE),
        lambda: preemptive_priority(SAMPLE),
        lambda: round_robin(SAMPLE, 2),
    ]
    expected_burst = sum(p["burst"] for p in SAMPLE)
    for run in algorithms:
        results, timeline = run()
        actual_burst = sum(e["finish"] - e["start"] for e in timeline)
        assert actual_burst == expected_burst
        assert all(p["turnaround"] == p["completion"] - p["arrival"] for p in results)
        assert all(p["waiting"] == p["turnaround"] - p["burst"] for p in results)


@pytest.mark.parametrize("bad_processes", [
    [{"pid": "P1", "arrival": -1, "burst": 2}],
    [{"pid": "P1", "arrival": 0, "burst": 0}],
    [{"pid": "P1", "arrival": 0, "burst": 2}, {"pid": "P1", "arrival": 1, "burst": 1}],
])
def test_invalid_process_data_is_rejected(bad_processes):
    with pytest.raises(ValueError):
        fcfs(bad_processes)


def test_preemptive_algorithms_handle_idle_gaps():
    processes = [
        {"pid": "P1", "arrival": 2, "burst": 1},
        {"pid": "P2", "arrival": 7, "burst": 2},
    ]
    for algorithm in (srtf, preemptive_priority):
        _, timeline = algorithm(processes)
        assert timeline == [
            {"pid": "P1", "start": 2, "finish": 3},
            {"pid": "P2", "start": 7, "finish": 9},
        ]
