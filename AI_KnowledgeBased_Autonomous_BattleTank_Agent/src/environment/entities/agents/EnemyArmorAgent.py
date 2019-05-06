from environment.entities.agents.ArmoredVehicleAgent import ArmoredVehicleAgent

class EnemyArmorAgent(ArmoredVehicleAgent):
    """
        :author: Aniruddha Kalburgi
        """

    def __init__(self, _location=0, _range=1, _health=1, _name = "EnemyArmor", _team="2", char_string = "ENM_T"):
        super().__init__(_range=_range, _location=_location, _health=_health, _name=_name, _team=_team)
        self.char_string = char_string
