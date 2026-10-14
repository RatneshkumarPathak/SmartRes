
from collections import deque


def fcfs(processes):
    """
    processes: list of dictionaries with:
    pid, arrival, burst
    """
    jobs = sorted(processes, key=lambda p: (p["arrival"], p["pid"]))
    time = 0
    results = []
    timeline = []

    for p in jobs:
        start = max(time, p["arrival"])
        finish = start + p["burst"]

        results.append({
            "pid": p["pid"],
            "arrival": p["arrival"],
            "burst": p["burst"],
            "start": start,
            "completion": finish,
            "turnaround": finish - p["arrival"],
            "waiting": start - p["arrival"],
        })

        timeline.append({
            "pid": p["pid"],
            "start": start,
            "finish": finish,
        })
        time = finish

    return results, timeline


def round_robin(processes, quantum):
    if quantum <= 0:
        raise ValueError("Time quantum must be greater than zero.")

    jobs = sorted(processes, key=lambda p: (p["arrival"], p["pid"]))
    remaining = {p["pid"]: p["burst"] for p in jobs}
    completion = {}
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

        p = ready.popleft()
        pid = p["pid"]
        run_time = min(quantum, remaining[pid])
        start = time
        time += run_time
        remaining[pid] -= run_time

        timeline.append({
            "pid": pid,
            "start": start,
            "finish": time,
        })

        while i < len(jobs) and jobs[i]["arrival"] <= time:
            ready.append(jobs[i])
            i += 1

        if remaining[pid] > 0:
            ready.append(p)
        else:
            completion[pid] = time

    results = []
    for p in jobs:
        turnaround = completion[p["pid"]] - p["arrival"]
        results.append({
            "pid": p["pid"],
            "arrival": p["arrival"],
            "burst": p["burst"],
            "completion": completion[p["pid"]],
            "turnaround": turnaround,
            "waiting": turnaround - p["burst"],
        })

    return results, timeline