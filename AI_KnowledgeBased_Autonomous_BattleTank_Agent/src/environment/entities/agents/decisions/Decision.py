
"""
:author Aniruddha Kalburgi
"""
class Decision:

    def __init__(self, _item, _action, _source_location, _target_location, _priority_score, _survival_threshold = 3):
        self.item = _item
        self.cycles_survived = 0
        self.cycles_survival_threshold = _survival_threshold
        self.action = _action
        self.source_location = _source_location
        self.target_location = _target_location
        self.priority_score = _priority_score #TODO sort decisions in the queue according to the priority score,
                                                # find shortest distance between the top item and this agent item
                                                # go to that location and perform an action while continuing scanning on the way
                                                # if something of more priority is added on the way, then again re-sort the priority list and
                                                # then visit the top priority item again

    def update_cycle_survival_history(self):
        self.cycles_survived += 1

    def trigger_cycle(self):
        if self.cycles_survived >= self.cycles_survival_threshold:
            self.priority_score += 1
