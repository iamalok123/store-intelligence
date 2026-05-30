import pytest
from pipeline.zones import (
    point_in_polygon,
    bbox_center,
    crossed_entry_line,
    determine_direction
)

def test_point_inside_polygon():
    polygon = [[100, 100], [400, 100], [400, 400], [100, 400]]
    point = (200, 200)
    assert point_in_polygon(point, polygon) is True

def test_point_outside_polygon():
    polygon = [[100, 100], [400, 100], [400, 400], [100, 400]]
    point = (50, 50)
    assert point_in_polygon(point, polygon) is False

def test_bbox_bottom_center():
    bbox = [100, 200, 300, 400]
    assert bbox_center(bbox) == (200.0, 400.0)

def test_entry_line_crossing_direction():
    # line from (0, 100) to (200, 100)
    line = [(0, 100), (200, 100)]
    
    # prev is above line (y=50), curr is below line (y=150)
    # y increases, so it crosses 'ENTRY' based on our simple heuristic
    prev_point = (100, 50)
    curr_point = (100, 150)
    
    assert crossed_entry_line(prev_point, curr_point, line) is True
    assert determine_direction(prev_point, curr_point, line) == "ENTRY"
    
    # prev is below line (y=150), curr is above line (y=50)
    # y decreases, so it crosses 'EXIT'
    prev_point2 = (100, 150)
    curr_point2 = (100, 50)
    
    assert crossed_entry_line(prev_point2, curr_point2, line) is True
    assert determine_direction(prev_point2, curr_point2, line) == "EXIT"
