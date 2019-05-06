class EnvironmentEntity:
    """
        :author: Aniruddha Kalburgi
        """

    def __init__(self, _location, _health, _name="Environment Entity", _is_static=True, _char_string = "EE"):
        self.location = _location
        self.health = _health
        self.name = _name
        self.is_static = True
        self.char_string = _char_string

    def relocate(self, _new_location):
        self.location = _new_location

    def is_alive(self):
        return self.health > 0

    def get_stats(self):
        return "%s" % self.name + " at location: %s" % str(self.location) + ", health:%d" % self.health

    def is_static_entity(self):
        return self.is_static

    def get_char_string(self):
        return self.char_string
