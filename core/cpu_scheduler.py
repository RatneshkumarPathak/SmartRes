from collections import deque


def _prepare_processes(processes):
    """Validate and return independent, deterministically ordered process records."""
    if not processes:
        raise ValueError("At least one process is required.")

    jobs = []
    seen_pids = set()

    for process in processes:
        if not isinstance(process, dict):
            raise ValueError("Each process must be a dictionary.")

        if "pid" not in process or process["pid"] is None or str(process["pid"]).strip() == "":
            raise ValueError("Every process must have a non-empty PID.")

        pid = process["pid"]
        if pid in seen_pids:
            raise ValueError(f"Duplicate process ID: {pid}")
        seen_pids.add(pid)

        arrival = process.get("arrival")
        burst = process.get("burst")
        priority = process.get("priority", 0)

        for field, value in (("arrival", arrival), ("burst", burst), ("priority", priority)):
            if isinstance(value, bool) or not isinstance(value, int):
                raise ValueError(f"{field.capitalize()} time and priority must be integers.")

        if arrival < 0:
            raise ValueError("Arrival time cannot be negative.")
        if burst <= 0:
            raise ValueError("Burst time must be greater than zero.")

        jobs.append({
            "pid": pid,
            "arrival": arrival,
            "burst": burst,
            "priority": priority,
        })

    # Keep the original project's arrival-then-PID ordering convention.
    return sorted(jobs, key=lambda p: (p["arrival"], str(p["pid"])))


def _build_results(jobs, completion, first_start):
    """Build a consistent result row for every scheduling algorithm."""
    results = []
    for process in jobs:
        pid = process["pid"]
        turnaround = completion[pid] - process["arrival"]
        results.append({
            "pid": pid,
            "arrival": process["arrival"],
            "burst": process["burst"],
            "priority": process["priority"],
            "start": first_start[pid],
            "completion": completion[pid],
            "turnaround": turnaround,
            "waiting": turnaround - process["burst"],
        })
    return results


def fcfs(processes):
    """First Come, First Served (non-preemptive)."""
    jobs = _prepare_processes(processes)
    time = 0
    results = []
    timeline = []

    for process in jobs:
        start = max(time, process["arrival"])
        finish = start + process["burst"]

        results.append({
            "pid": process["pid"],
            "arrival": process["arrival"],
            "burst": process["burst"],
            "priority": process["priority"],
            "start": start,
            "completion": finish,
            "turnaround": finish - process["arrival"],
            "waiting": start - process["arrival"],
        })
        timeline.append({"pid": process["pid"], "start": start, "finish": finish})
        time = finish

    return results, timeline


def _non_preemptive(processes, selection_key):
    """Shared engine for non-preemptive SJF and Priority scheduling."""
    jobs = _prepare_processes(processes)
    pending = list(jobs)
    time = 0
    completion = {}
    first_start = {}
    timeline = []

    while pending:
        ready = [p for p in pending if p["arrival"] <= time]

        if not ready:
            time = min(p["arrival"] for p in pending)
            ready = [p for p in pending if p["arrival"] <= time]

        selected = min(ready, key=selection_key)
        pending.remove(selected)

        start = time
        finish = start + selected["burst"]
        first_start[selected["pid"]] = start
        completion[selected["pid"]] = finish
        timeline.append({"pid": selected["pid"], "start": start, "finish": finish})
        time = finish

    return _build_results(jobs, completion, first_start), timeline


def sjf(processes):
    """Shortest Job First, non-preemptive; ties use arrival time then PID."""
    return _non_preemptive(
        processes,
        lambda p: (p["burst"], p["arrival"], str(p["pid"])),
    )


def priority_scheduling(processes):
    """Priority scheduling, non-preemptive; smaller number means higher priority."""
    return _non_preemptive(
        processes,
        lambda p: (p["priority"], p["arrival"], str(p["pid"])),
    )


def _preemptive(processes, selection_key):
    """Unit-time preemptive scheduler used by SRTF and preemptive Priority."""
    jobs = _prepare_processes(processes)
    remaining = {p["pid"]: p["burst"] for p in jobs}
    completion = {}
    first_start = {}
    timeline = []
    time = 0
    finished_count = 0

    while finished_count < len(jobs):
        ready = [
            p for p in jobs
            if p["arrival"] <= time and remaining[p["pid"]] > 0
        ]

        if not ready:
            future_arrivals = [p["arrival"] for p in jobs if remaining[p["pid"]] > 0]
            time = min(future_arrivals)
            continue

        selected = min(ready, key=selection_key(remaining))
        pid = selected["pid"]
        first_start.setdefault(pid, time)

        # Run for one time unit, then reconsider the ready processes.
        start = time
        time += 1
        remaining[pid] -= 1

        # Merge consecutive units by the same process into one Gantt segment.
        if timeline and timeline[-1]["pid"] == pid and timeline[-1]["finish"] == start:
            timeline[-1]["finish"] = time
        else:
            timeline.append({"pid": pid, "start": start, "finish": time})

        if remaining[pid] == 0:
            completion[pid] = time
            finished_count += 1

    return _build_results(jobs, completion, first_start), timeline


def srtf(processes):
    """Shortest Remaining Time First (preemptive SJF)."""
    return _preemptive(
        processes,
        lambda remaining: lambda p: (
            remaining[p["pid"]], p["arrival"], str(p["pid"])
        ),
    )


def preemptive_priority(processes):
    """Preemptive Priority; smaller number means higher priority."""
    return _preemptive(
        processes,
        lambda remaining: lambda p: (
            p["priority"], p["arrival"], str(p["pid"])
        ),
    )


def round_robin(processes, quantum):
    """Round Robin scheduling with arrivals added before the expired job is re-queued."""
    if isinstance(quantum, bool) or not isinstance(quantum, int) or quantum <= 0:
        raise ValueError("Time quantum must be a positive integer.")

    jobs = _prepare_processes(processes)
    remaining = {p["pid"]: p["burst"] for p in jobs}
    completion = {}
    first_start = {}
    timeline = []
    ready = deque()
    time = 0
    i = 0

    while i < len(jobs) or ready:
        if not ready and i < len(jobs) and time < jobs[i]["arrival"]:
            time = jobs[i]["arrival"]

        while i < len(jobs) and jobs[i]["arrival"] <= time:
            ready.append(jobs[i])
            i += 1

        if not ready:
            continue

        process = ready.popleft()
        pid = process["pid"]
        first_start.setdefault(pid, time)

        run_time = min(quantum, remaining[pid])
        start = time
        time += run_time
        remaining[pid] -= run_time

        # Keep each quantum as a separate event for step-by-step playback.
        timeline.append({"pid": pid, "start": start, "finish": time})

        # New arrivals join the queue before the unfinished process returns.
        while i < len(jobs) and jobs[i]["arrival"] <= time:
            ready.append(jobs[i])
            i += 1

        if remaining[pid] > 0:
            ready.append(process)
        else:
            completion[pid] = time

    return _build_results(jobs, completion, first_start), timeline
