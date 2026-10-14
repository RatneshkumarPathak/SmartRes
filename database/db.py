
import sqlite3
from pathlib import Path
from datetime import datetime

from core.bankers_algorithm import evaluate_request

DB_PATH = Path(__file__).resolve().parent / "smartres.db"


def connect():
    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db():
    with connect() as db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS resources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                total INTEGER NOT NULL CHECK (total >= 0)
            );

            CREATE TABLE IF NOT EXISTS processes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Active'
                    CHECK (status IN ('Active', 'Terminated')),
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS allocations (
                process_id INTEGER NOT NULL,
                resource_id INTEGER NOT NULL,
                max_claim INTEGER NOT NULL CHECK (max_claim >= 0),
                allocated INTEGER NOT NULL DEFAULT 0
                    CHECK (allocated >= 0),
                PRIMARY KEY (process_id, resource_id),
                FOREIGN KEY (process_id) REFERENCES processes(id),
                FOREIGN KEY (resource_id) REFERENCES resources(id),
                CHECK (allocated <= max_claim)
            );

            CREATE TABLE IF NOT EXISTS event_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                event_type TEXT NOT NULL,
                details TEXT NOT NULL
            );
        """)


def log_event(db, event_type, details):
    db.execute(
        """INSERT INTO event_logs (timestamp, event_type, details)
           VALUES (?, ?, ?)""",
        (datetime.now().isoformat(timespec="seconds"), event_type, details),
    )


def get_resources():
    with connect() as db:
        return [dict(row) for row in db.execute(
            "SELECT id, name, total FROM resources ORDER BY id"
        )]


def get_processes():
    with connect() as db:
        return [dict(row) for row in db.execute(
            """SELECT id, name, status, created_at
               FROM processes ORDER BY id DESC"""
        )]


def get_allocations():
    with connect() as db:
        return [dict(row) for row in db.execute("""
            SELECT p.id AS process_id, p.name AS process,
                   p.status, r.id AS resource_id, r.name AS resource,
                   a.max_claim, a.allocated,
                   a.max_claim - a.allocated AS need
            FROM allocations a
            JOIN processes p ON p.id = a.process_id
            JOIN resources r ON r.id = a.resource_id
            ORDER BY p.id, r.id
        """)]


def get_events(limit=100):
    with connect() as db:
        return [dict(row) for row in db.execute(
            """SELECT timestamp, event_type, details
               FROM event_logs ORDER BY id DESC LIMIT ?""",
            (limit,),
        )]



def add_resource(name, total):
    name = name.strip()
    if not name:
        raise ValueError("Resource name cannot be empty.")
    if total < 0:
        raise ValueError("Resource total cannot be negative.")

    with connect() as db:
        cursor = db.execute(
            "INSERT INTO resources (name, total) VALUES (?, ?)",
            (name, total),
        )
        resource_id = cursor.lastrowid

        # Add a zero-allocation entry for every existing process.
        existing_processes = db.execute(
            "SELECT id FROM processes"
        ).fetchall()

        for process in existing_processes:
            db.execute(
                """INSERT INTO allocations
                   (process_id, resource_id, max_claim, allocated)
                   VALUES (?, ?, 0, 0)""",
                (process["id"], resource_id),
            )

        log_event(db, "RESOURCE_CREATED", f"{name}: total={total}")


def update_resource_total(resource_id, total):
    if total < 0:
        raise ValueError("Total cannot be negative.")

    with connect() as db:
        row = db.execute(
            "SELECT name FROM resources WHERE id = ?", (resource_id,)
        ).fetchone()
        if row is None:
            raise ValueError("Resource not found.")

        allocated = db.execute(
            """SELECT COALESCE(SUM(allocated), 0)
               FROM allocations WHERE resource_id = ?""",
            (resource_id,),
        ).fetchone()[0]

        if total < allocated:
            raise ValueError(
                f"Total cannot be below the {allocated} units already allocated."
            )

        db.execute(
            "UPDATE resources SET total = ? WHERE id = ?",
            (total, resource_id),
        )
        log_event(db, "RESOURCE_UPDATED", f"{row['name']}: total={total}")


def add_process(name, maximum_claims):
    name = name.strip()
    if not name:
        raise ValueError("Process name cannot be empty.")

    resources = get_resources()
    if not resources:
        raise ValueError("Create at least one resource before adding a process.")

    resource_ids = {r["id"] for r in resources}
    if set(maximum_claims) != resource_ids:
        raise ValueError("Provide a maximum claim for every resource.")

    for resource in resources:
        claim = maximum_claims[resource["id"]]
        if claim < 0 or claim > resource["total"]:
            raise ValueError(
                f"Maximum claim for {resource['name']} must be between "
                f"0 and {resource['total']}."
            )

    with connect() as db:
        cursor = db.execute(
            """INSERT INTO processes (name, status, created_at)
               VALUES (?, 'Active', ?)""",
            (name, datetime.now().isoformat(timespec="seconds")),
        )
        process_id = cursor.lastrowid

        for resource in resources:
            db.execute(
                """INSERT INTO allocations
                   (process_id, resource_id, max_claim, allocated)
                   VALUES (?, ?, ?, 0)""",
                (
                    process_id,
                    resource["id"],
                    maximum_claims[resource["id"]],
                ),
            )

        log_event(db, "PROCESS_CREATED", f"Process {name} (P{process_id}) created.")


def _banker_state(db):
    resources = db.execute(
        "SELECT id, total FROM resources ORDER BY id"
    ).fetchall()
    processes = db.execute(
        """SELECT id FROM processes WHERE status = 'Active' ORDER BY id"""
    ).fetchall()

    resource_ids = [r["id"] for r in resources]
    process_ids = [p["id"] for p in processes]

    allocation = []
    need = []
    allocated_totals = [0] * len(resource_ids)

    for process_id in process_ids:
        rows = db.execute(
            """SELECT resource_id, max_claim, allocated
               FROM allocations WHERE process_id = ?""",
            (process_id,),
        ).fetchall()
        by_resource = {row["resource_id"]: row for row in rows}

        allocation_row = []
        need_row = []
        for index, resource_id in enumerate(resource_ids):
            row = by_resource[resource_id]
            allocation_row.append(row["allocated"])
            need_row.append(row["max_claim"] - row["allocated"])
            allocated_totals[index] += row["allocated"]

        allocation.append(allocation_row)
        need.append(need_row)

    available = [
        resources[i]["total"] - allocated_totals[i]
        for i in range(len(resources))
    ]
    return resource_ids, process_ids, available, allocation, need


def get_safety_status():
    from core.bankers_algorithm import is_safe_state

    with connect() as db:
        _, process_ids, available, allocation, need = _banker_state(db)
        safe, sequence = is_safe_state(available, allocation, need)
        return {
            "safe": safe,
            "sequence": [process_ids[i] for i in sequence],
            "available": available,
        }


def request_resources(process_id, resource_id, amount):
    if amount <= 0:
        return False, "Request must be at least one unit.", []

    with connect() as db:
        process = db.execute(
            "SELECT name, status FROM processes WHERE id = ?",
            (process_id,),
        ).fetchone()
        resource = db.execute(
            "SELECT name FROM resources WHERE id = ?", (resource_id,)
        ).fetchone()

        if process is None or resource is None:
            return False, "Process or resource not found.", []
        if process["status"] != "Active":
            return False, "Terminated processes cannot request resources.", []

        ids, process_ids, available, allocation, need = _banker_state(db)

        if resource_id not in ids or process_id not in process_ids:
            return False, "Process or resource is not active.", []

        p_index = process_ids.index(process_id)
        r_index = ids.index(resource_id)
        request = [0] * len(ids)
        request[r_index] = amount

        approved, reason, sequence = evaluate_request(
            available, allocation, need, p_index, request
        )

        log_event(
            db,
            "REQUEST_APPROVED" if approved else "REQUEST_REJECTED",
            f"{process['name']} requested {amount} of {resource['name']}: {reason}",
        )

        if not approved:
            return False, reason, []

        db.execute(
            """UPDATE allocations SET allocated = allocated + ?
               WHERE process_id = ? AND resource_id = ?""",
            (amount, process_id, resource_id),
        )

        safe_sequence = [process_ids[i] for i in sequence]
        return True, reason, safe_sequence


def terminate_process(process_id):
    with connect() as db:
        process = db.execute(
            "SELECT name, status FROM processes WHERE id = ?",
            (process_id,),
        ).fetchone()

        if process is None:
            raise ValueError("Process not found.")
        if process["status"] != "Active":
            raise ValueError("Process is already terminated.")

        db.execute(
            "UPDATE allocations SET allocated = 0 WHERE process_id = ?",
            (process_id,),
        )
        db.execute(
            "UPDATE processes SET status = 'Terminated' WHERE id = ?",
            (process_id,),
        )
        log_event(
            db,
            "PROCESS_TERMINATED",
            f"{process['name']} terminated; allocated resources released.",
        )