from src.fieldservice_usage import WorkOrderPhoto, billable_units


def test_follow_up_is_counted_only_after_dispatch():
    dispatched = WorkOrderPhoto("shop-104", "wo-1", 3, True, True)
    waiting = WorkOrderPhoto("shop-104", "wo-2", 3, False, True)
    assert billable_units(dispatched) == 4
    assert billable_units(waiting) == 3
