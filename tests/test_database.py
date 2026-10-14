
import database.db as database


def setup_test_db(tmp_path, monkeypatch):
    """Give each test its own isolated database."""
    test_db = tmp_path / "smartres_test.db"
    monkeypatch.setattr(database, "DB_PATH", test_db)
    database.init_db()
    return test_db


def test_resources_and_processes_persist(tmp_path, monkeypatch):
    setup_test_db(tmp_path, monkeypatch)

    database.add_resource("CPU", 3)
    resource = database.get_resources()[0]

    database.add_process(
        "Process A",
        {resource["id"]: 2},
    )

    # These functions open new database connections.
    assert len(database.get_resources()) == 1
    processes = database.get_processes()
    assert len(processes) == 1
    assert processes[0]["name"] == "Process A"

    allocations = database.get_allocations()
    assert len(allocations) == 1
    assert allocations[0]["max_claim"] == 2
    assert allocations[0]["allocated"] == 0


def test_approved_request_updates_allocation(tmp_path, monkeypatch):
    setup_test_db(tmp_path, monkeypatch)

    database.add_resource("CPU", 3)
    resource = database.get_resources()[0]
    database.add_process("Process A", {resource["id"]: 2})
    process = database.get_processes()[0]

    approved, reason, sequence = database.request_resources(
        process["id"], resource["id"], 1
    )

    assert approved is True
    assert sequence == [process["id"]]

    allocation = database.get_allocations()[0]
    assert allocation["allocated"] == 1
    assert allocation["need"] == 1


def test_unsafe_request_does_not_change_allocations(
    tmp_path, monkeypatch
):
    setup_test_db(tmp_path, monkeypatch)

    database.add_resource("R", 3)
    resource = database.get_resources()[0]
    rid = resource["id"]

    database.add_process("P1", {rid: 3})
    database.add_process("P2", {rid: 2})

    processes = {
        process["name"]: process["id"]
        for process in database.get_processes()
    }

    # Establish a safe state with one unit allocated to each process.
    approved1, _, _ = database.request_resources(
        processes["P1"], rid, 1
    )
    approved2, _, _ = database.request_resources(
        processes["P2"], rid, 1
    )
    assert approved1 is True
    assert approved2 is True

    before = database.get_allocations()

    # No units are available. Granting one to P1 would make the
    # state unsafe because both processes would still need one unit.
    approved, reason, _ = database.request_resources(
        processes["P1"], rid, 1
    )

    after = database.get_allocations()

    assert approved is False
    assert "unsafe" in reason.lower()
    assert after == before


def test_terminating_process_releases_resources(
    tmp_path, monkeypatch
):
    setup_test_db(tmp_path, monkeypatch)

    database.add_resource("RAM", 4)
    resource = database.get_resources()[0]
    database.add_process("Worker", {resource["id"]: 3})
    process = database.get_processes()[0]

    approved, _, _ = database.request_resources(
        process["id"], resource["id"], 2
    )
    assert approved is True

    database.terminate_process(process["id"])

    allocation = database.get_allocations()[0]
    assert allocation["allocated"] == 0
    assert allocation["need"] == 3

    updated_process = next(
        p for p in database.get_processes()
        if p["id"] == process["id"]
    )
    assert updated_process["status"] == "Terminated"

    # The released RAM is available again.
    safety = database.get_safety_status()
    assert safety["available"] == [4]
