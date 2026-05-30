from pipeline.emit import make_event
from pipeline.zones import crossed_entry_line, determine_direction

class VisitorStateTracker:
    def __init__(self, store_id, camera_id):
        self.store_id = store_id
        self.camera_id = camera_id
        self.visitor_state = {}
        # {
        #   visitor_id: {
        #     "inside": False,
        #     "last_zone": None,
        #     "last_point": None
        #   }
        # }
        
    def _get_state(self, visitor_id):
        if visitor_id not in self.visitor_state:
            self.visitor_state[visitor_id] = {
                "inside": False,
                "last_zone": None,
                "last_point": None
            }
        return self.visitor_state[visitor_id]

    def update_position(self, visitor_id, current_point, timestamp, entry_line=None):
        """
        Updates the position for a visitor and generates ENTRY/EXIT events if an entry line is provided.
        Returns a list of generated events.
        """
        state = self._get_state(visitor_id)
        events = []
        
        last_point = state["last_point"]
        
        if entry_line and last_point:
            if crossed_entry_line(last_point, current_point, entry_line):
                direction = determine_direction(last_point, current_point, entry_line)
                
                if direction == "ENTRY" and not state["inside"]:
                    state["inside"] = True
                    events.append(make_event(self.store_id, self.camera_id, visitor_id, "ENTRY", timestamp))
                elif direction == "EXIT" and state["inside"]:
                    state["inside"] = False
                    events.append(make_event(self.store_id, self.camera_id, visitor_id, "EXIT", timestamp))

        state["last_point"] = current_point
        return events

    def update_zone(self, visitor_id, current_zone, timestamp):
        """
        Updates the zone for a visitor and generates ZONE_ENTER/ZONE_EXIT events.
        Returns a list of generated events.
        """
        state = self._get_state(visitor_id)
        events = []
        
        last_zone = state["last_zone"]
        
        if last_zone != current_zone:
            if last_zone is not None:
                events.append(make_event(self.store_id, self.camera_id, visitor_id, "ZONE_EXIT", timestamp, zone_id=last_zone))
            if current_zone is not None:
                events.append(make_event(self.store_id, self.camera_id, visitor_id, "ZONE_ENTER", timestamp, zone_id=current_zone))
                
        state["last_zone"] = current_zone
        return events
