
-- Report 1: Process register and status
SELECT
    process_id,
    process_name,
    process_status,
    created_at
FROM sr_processes
ORDER BY process_id;

-- Report 2: Resource utilization
SELECT
    r.resource_id,
    r.resource_name,
    r.total_units,
    NVL(SUM(a.allocated_units), 0) AS allocated_units,
    r.total_units - NVL(SUM(a.allocated_units), 0) AS available_units,
    CASE
        WHEN r.total_units = 0 THEN 0
        ELSE ROUND(
            100 * NVL(SUM(a.allocated_units), 0) / r.total_units,
            2
        )
    END AS utilization_percent
FROM sr_resources r
LEFT JOIN sr_allocations a
    ON r.resource_id = a.resource_id
GROUP BY r.resource_id, r.resource_name, r.total_units
ORDER BY r.resource_id;

-- Report 3: Allocation and remaining need for each process
SELECT
    p.process_id,
    p.process_name,
    p.process_status,
    r.resource_name,
    a.max_claim,
    a.allocated_units,
    a.max_claim - a.allocated_units AS remaining_need
FROM sr_processes p
JOIN sr_allocations a
    ON p.process_id = a.process_id
JOIN sr_resources r
    ON a.resource_id = r.resource_id
ORDER BY p.process_id, r.resource_id;

-- Report 4: Resource request history
SELECT
    q.request_id,
    p.process_name,
    r.resource_name,
    q.requested_units,
    q.request_status,
    q.reason,
    q.requested_at
FROM sr_requests q
JOIN sr_processes p
    ON q.process_id = p.process_id
JOIN sr_resources r
    ON q.resource_id = r.resource_id
ORDER BY q.requested_at DESC, q.request_id DESC;

-- Report 5: Processes with the highest total allocation
SELECT
    p.process_id,
    p.process_name,
    SUM(a.allocated_units) AS total_units_allocated
FROM sr_processes p
JOIN sr_allocations a
    ON p.process_id = a.process_id
GROUP BY p.process_id, p.process_name
HAVING SUM(a.allocated_units) > 0
ORDER BY total_units_allocated DESC;

-- Report 6: Recent system events
SELECT
    event_id,
    event_type,
    details,
    event_time
FROM sr_event_logs
ORDER BY event_time DESC, event_id DESC;