from environment.entities.agents.ArmoredVehicleAgent import ArmoredVehicleAgent


class BattleTankAgent(ArmoredVehicleAgent):
    """
    :author: Aniruddha Kalburgi
    """

    # the range for Player's bot agent has to be 2 or higher, otherwise entering enemy range of 1 makes player-agent susceptible to get shot by the enemy-agent
    def __init__(self, _range=2, _location=0, _health=1, _name = "BattleTank", _team="1", char_string = "PLR_T"):
        super().__init__(_range=_range, _location=_location, _health=_health, _name=_name, _team=_team, char_string=char_string)
        self.char_string = char_string
