def is_safe_state(available, allocation, need):
    """
    Check whether the current resource-allocation state is safe.

    available:  list[int]
    allocation: list[list[int]]
    need:       list[list[int]]

    Returns:
        (is_safe, safe_sequence)
    """
    process_count = len(allocation)
    resource_count = len(available)

    if len(need) != process_count:
        raise ValueError("Allocation and need must have the same process count.")

    if any(len(row) != resource_count for row in allocation + need):
        raise ValueError("Every allocation and need row must match the resource count.")

    if any(value < 0 for value in available):
        raise ValueError("Available resource counts cannot be negative.")

    if any(value < 0 for row in allocation + need for value in row):
        raise ValueError("Allocation and need values cannot be negative.")

    work = available.copy()
    finished = [False] * process_count
    safe_sequence = []

    while len(safe_sequence) < process_count:
        progress = False

        for process_index in range(process_count):
            if finished[process_index]:
                continue

            can_finish = all(
                need[process_index][resource_index]
                <= work[resource_index]
                for resource_index in range(resource_count)
            )

            if can_finish:
                for resource_index in range(resource_count):
                    work[resource_index] += allocation[process_index][resource_index]

                finished[process_index] = True
                safe_sequence.append(process_index)
                progress = True

        if not progress:
            return False, []

    return True, safe_sequence


def evaluate_request(
    available,
    allocation,
    need,
    process_index,
    request,
):
    """
    Evaluate a resource request without permanently changing the input data.

    Returns (approved, reason, safe_sequence).
    """
    if not 0 <= process_index < len(allocation):
        return False, "Invalid process.", []

    if len(request) != len(available):
        return False, "Request has the wrong number of resource types.", []

    if any(value < 0 for value in request):
        return False, "Resource requests cannot be negative.", []

    if any(
        request[i] > need[process_index][i]
        for i in range(len(available))
    ):
        return False, "Request exceeds the process's declared maximum claim.", []

    if any(
        request[i] > available[i]
        for i in range(len(available))
    ):
        return False, "Insufficient currently available resources.", []

    # Simulate granting the request.
    new_available = [
        available[i] - request[i]
        for i in range(len(available))
    ]

    new_allocation = [row.copy() for row in allocation]
    new_need = [row.copy() for row in need]

    for i in range(len(available)):
        new_allocation[process_index][i] += request[i]
        new_need[process_index][i] -= request[i]

    safe, sequence = is_safe_state(
        new_available,
        new_allocation,
        new_need,
    )

    if not safe:
        return False, "Request would leave the system in an unsafe state.", []

    return True, "Request approved: system remains in a safe state.", sequence
