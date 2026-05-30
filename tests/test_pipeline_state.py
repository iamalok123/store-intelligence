import pytest
from datetime import datetime, UTC
from pipeline.state import VisitorStateTracker

def test_entry_exit_generation():
    tracker = VisitorStateTracker("STORE_1", "CAM_1")
    visitor_id = "VIS_01"
    entry_line = [(0, 100), (200, 100)]
    ts = datetime.now(UTC)

    # Initial position above line (outside)
    events = tracker.update_position(visitor_id, (100, 50), ts, entry_line)
    assert len(events) == 0

    # Cross line downward (ENTRY)
    events = tracker.update_position(visitor_id, (100, 150), ts, entry_line)
    assert len(events) == 1
    assert events[0]["event_type"] == "ENTRY"

    # Stay inside
    events = tracker.update_position(visitor_id, (100, 160), ts, entry_line)
    assert len(events) == 0

    # Cross line upward (EXIT)
    events = tracker.update_position(visitor_id, (100, 50), ts, entry_line)
    assert len(events) == 1
    assert events[0]["event_type"] == "EXIT"

def test_zone_generation():
    tracker = VisitorStateTracker("STORE_1", "CAM_1")
    visitor_id = "VIS_01"
    ts = datetime.now(UTC)

    # None -> SKINCARE
    events = tracker.update_zone(visitor_id, "SKINCARE", ts)
    assert len(events) == 1
    assert events[0]["event_type"] == "ZONE_ENTER"
    assert events[0]["zone_id"] == "SKINCARE"

    # SKINCARE -> MAKEUP
    events = tracker.update_zone(visitor_id, "MAKEUP", ts)
    assert len(events) == 2
    assert events[0]["event_type"] == "ZONE_EXIT"
    assert events[0]["zone_id"] == "SKINCARE"
    assert events[1]["event_type"] == "ZONE_ENTER"
    assert events[1]["zone_id"] == "MAKEUP"

    # MAKEUP -> None
    events = tracker.update_zone(visitor_id, None, ts)
    assert len(events) == 1
    assert events[0]["event_type"] == "ZONE_EXIT"
    assert events[0]["zone_id"] == "MAKEUP"
