from environment.entities.EnvironmentEntity import EnvironmentEntity


class AmmoType(EnvironmentEntity):
    """
        :author: Aniruddha Kalburgi
        """

    TANK_BULLETS = 1
    AT_MISSILE = 10
    DEFAULT = TANK_BULLETS

    def __init__(self, _ammo_count=5, _location=0, _ammo_type=DEFAULT, char_string="AMO"):
        super().__init__(_location=_location, _health=1, _name="Ammo", _char_string=char_string)
        self.ammo_count = _ammo_count
        self.location = _location
        self.ammo_type = _ammo_type

    def relocate(self, new_location):
        self.location = new_location

    def get_ammo_count(self):
        return self.ammo_count

    def get_ammo_strength(self):
        return self.ammo_type
