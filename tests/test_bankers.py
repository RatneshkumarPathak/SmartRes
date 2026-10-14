
from core.bankers_algorithm import is_safe_state, evaluate_request


def test_safe_state_returns_a_valid_sequence():
    available = [3, 3, 2]

    allocation = [
        [0, 1, 0],
        [2, 0, 0],
        [3, 0, 2],
        [2, 1, 1],
        [0, 0, 2],
    ]

    need = [
        [7, 4, 3],
        [1, 2, 2],
        [6, 0, 0],
        [0, 1, 1],
        [4, 3, 1],
    ]

    safe, sequence = is_safe_state(available, allocation, need)

    assert safe is True
    assert sorted(sequence) == [0, 1, 2, 3, 4]


def test_unsafe_state_is_rejected():
    available = [0]
    allocation = [[1], [0]]
    need = [[1], [1]]

    safe, sequence = is_safe_state(available, allocation, need)

    assert safe is False
    assert sequence == []


def test_request_approved_when_state_remains_safe():
    available = [3, 3, 2]
    allocation = [[0, 1, 0], [2, 0, 0]]
    need = [[2, 1, 1], [1, 2, 2]]

    approved, reason, sequence = evaluate_request(
        available, allocation, need, 0, [1, 0, 1]
    )

    assert approved is True
    assert "approved" in reason.lower()
    assert len(sequence) == 2


def test_request_exceeding_need_is_rejected():
    available = [3]
    allocation = [[0]]
    need = [[2]]

    approved, reason, sequence = evaluate_request(
        available, allocation, need, 0, [3]
    )

    assert approved is False
    assert "maximum claim" in reason.lower()
    assert sequence == []


def test_request_exceeding_available_is_rejected():
    available = [1]
    allocation = [[0]]
    need = [[2]]

    approved, reason, sequence = evaluate_request(
        available, allocation, need, 0, [2]
    )

    assert approved is False
    assert "available" in reason.lower()
    assert sequence == []