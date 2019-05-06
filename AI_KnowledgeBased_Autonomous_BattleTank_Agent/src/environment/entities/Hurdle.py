from environment.entities.EnvironmentEntity import EnvironmentEntity


class Hurdle(EnvironmentEntity):
    """
    :author: Aniruddha Kalburgi
    """

    def __init__(self, _location=0, _health=2, char_string="HUR"):
        super().__init__(_location=_location, _health=_health, _name="Hurdle", _char_string=char_string)
        self.health = _health
