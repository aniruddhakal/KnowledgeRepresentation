from enum import Enum

from constants.AmmoTypes import AmmoType
from environment.entities.Hurdle import Hurdle
from environment.entities.agents.BattleTankAgent import BattleTankAgent
from environment.entities.agents.EnemyArmorAgent import EnemyArmorAgent


class Priorities(Enum):
    """
        :author: Aniruddha Kalburgi
        """

    FRIENDLY = 0
    MOVE_RIGHT = 2
    MOVE_LEFT = 2
    MOVE_UP = 2
    MOVE_DOWN = 2
    MOVE_TO_THE_TARGET = 6
    CROSS_HURDLE = 7
    COLLECT_AMMO = 8
    DESTROY_HURDLE = 9
    DESTROY_ENEMY = 10

    @staticmethod
    def getPriorityForThing(source_thing, target_thing):
        if type(source_thing) == type(target_thing):
            return Priorities.FRIENDLY
        elif (isinstance(source_thing, BattleTankAgent) and isinstance(target_thing, EnemyArmorAgent)) or isinstance(
                target_thing, BattleTankAgent) and isinstance(source_thing, EnemyArmorAgent):
            return Priorities.DESTROY_ENEMY
        elif isinstance(target_thing, AmmoType):
            return Priorities.COLLECT_AMMO
        elif isinstance(target_thing, Hurdle):
            return Priorities.DESTROY_HURDLE