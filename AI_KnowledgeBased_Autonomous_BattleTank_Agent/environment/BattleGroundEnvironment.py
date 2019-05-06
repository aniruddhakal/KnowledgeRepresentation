import random

import numpy as np

from constants.AmmoTypes import AmmoType
from environment.entities.Hurdle import Hurdle
from environment.entities.agents.ArmoredVehicleAgent import ArmoredVehicleAgent
from environment.entities.agents.BattleTankAgent import BattleTankAgent
from environment.entities.agents.EnemyArmorAgent import EnemyArmorAgent
from constants.Priorities import Priorities

"""
    :author: Aniruddha Kalburgi
    """


class BattleGround:

    # TODO redefine - block
    def __init__(self, _field_length=10):
        self.fieldWidth = _field_length
        self.battlefield = np.array([0] * self.fieldWidth)
        self.items_dictionary = {}
        self.enemies = list()
        self.global_enemies_total_health = 0
        self.good_players = list()
        self.global_good_players_total_health = 0
        self.good_player_turn = True
        self.priorities = Priorities

    def perceive(self, agent):
        """
        :return tuple (items at current location, array of items in range - but not at current location)
        """
        items_at_location = self.get_existing_items_at(agent.location)

        items_in_range = list()

        items_in_range.extend(self.perceiveItemsBehindAgent(agent))
        items_in_range.extend(self.perceiveItemsAheadAgent(agent))

        return items_at_location, items_in_range

    def perceiveItemsBehindAgent(self, agent):
        perceived_items = []

        difference = agent.location - agent.range

        start = 0
        end = agent.location

        if difference >= 0:
            # items within range behind the agent
            start = difference

        # perceived_items.extend(self.battlefield[start:end])
        for i in range(start, end):
            if i in self.items_dictionary:
                perceived_items.extend(self.items_dictionary[i])

        return perceived_items

    def perceiveItemsAheadAgent(self, agent):
        perceived_items = []

        # if agent isn't at the last/end location then perceive items ahead of the agent within its range
        last_position = len(self.battlefield) - 1
        if agent.location != (last_position):
            start = agent.location + 1
            end = start + agent.range

            difference = end - len(self.battlefield)
            if difference > 0:
                end -= difference

            for i in range(start, end):
                if i in self.items_dictionary:
                    perceived_items.extend(self.items_dictionary[i])

        return perceived_items

    def actionHappened(self):
        # TODO called when something is inserted, health updated, destroyed/killed etc
        # identify more events for actionHappened()
        # TODO each time this function is called, trigger change representation method and paint the current world state
        pass

    def get_random_available_location(self):
        random_location = -1
        available_indices = np.where(self.battlefield == 0)[0]

        if len(available_indices) > 0:
            random_location = random.choice(available_indices)

        return random_location

    def insert_thing(self, _location_index, _thing):
        existing_things = []
        inserted = False
        hurdle_exists = False
        ammo_exists = False
        armored_vehicle_exists = False

        if _location_index in self.items_dictionary:
            existing_things = self.items_dictionary[_location_index]

        if not isinstance(_thing, AmmoType) and _thing.health > 0:
            hurdle_exists = isinstance(_thing, Hurdle) and (self.already_exists(_thing, Hurdle, existing_things))
            armored_vehicle_exists = isinstance(_thing, ArmoredVehicleAgent) and (
                self.already_exists(_thing, ArmoredVehicleAgent, existing_things))

        if isinstance(_thing, AmmoType):  # separately handled because ammo doesn't have health
            ammo_exists = self.already_exists(_thing, AmmoType, existing_things)
            if ammo_exists:
                return inserted
            elif not hurdle_exists:
                inserted = self.insert(_thing, _location_index)
                return inserted

        # if not ((ammo_exists and not isinstance(_thing, Hurdle)) or hurdle_exists or armored_vehicle_exists):
        if not hurdle_exists:
            if not armored_vehicle_exists:
                inserted = self.insert(_thing, _location_index)

                if isinstance(_thing, EnemyArmorAgent):
                    self.enemies.append(_thing)
                    self.global_enemies_total_health += _thing.health
                elif isinstance(_thing, BattleTankAgent):
                    self.good_players.append(_thing)
                    self.global_good_players_total_health += _thing.health
            elif isinstance(_thing, Hurdle):
                print(
                    "Hurdle cannot be inserted at location %s as something already exists here" % str(_location_index))

        return inserted

    def update_location_availability(self, _location_index):
        existing_things = self.get_existing_items_at(_location_index)

        ammo_count = 0
        for item in existing_things:
            if isinstance(item, AmmoType):
                ammo_count += 1
                break

        self.battlefield[_location_index] = len(existing_things) - ammo_count

    def relocate_agent(self, thing, new_location_index):
        current_location = thing.location
        self.remove_item_at(current_location, thing)
        self.insert(thing, new_location_index)
        print("Agent movement: %s " % thing.get_stats() + "; from location:%s" % str(current_location))

    def insert(self, _thing, _location_index):
        existing_things = self.get_existing_items_at(location_index=_location_index)
        existing_things.append(_thing)
        self.items_dictionary[_location_index] = existing_things

        self.update_location_availability(_location_index)

        _thing.relocate(_location_index)

        # TODO decide if actionHappened() method should be called here or at the end of originating method call
        self.actionHappened()
        return True

    def already_exists(self, _thing, ClassTypeItem, things_list):
        similar_thing_doesnt_exists = False

        for item in things_list:
            if isinstance(item, AmmoType) and isinstance(_thing, AmmoType):
                return True
            elif isinstance(item, ClassTypeItem):
                return True

        return similar_thing_doesnt_exists

    def insert_generic_thing(self, _thing=None, _thing_type=None):
        if _thing is None and _thing_type is None:
            print("Please pass valid argument to insert_generic_thing(_thing or _target_method) method")
            return False

        inserted = False
        location_index = self.get_random_available_location()

        if _thing is None:
            _thing = self.identify_and_init_thing(_thing_type=_thing_type, location_index=location_index)

        if location_index == -1 and isinstance(_thing, AmmoType):
            location_index = random.choice([x for x in range(0, len(self.battlefield))])
        elif location_index == -1:
            print("Cannot insert the %s as no location is available" % _thing.name)
            return False

        inserted = self.insert_thing(_location_index=location_index, _thing=_thing)

        if inserted:
            print("Inserted the %s" % _thing.get_stats())
        else:
            print(
                "%s " % _thing.name + "cannot be inserted at location %s because something already exists there." % str(
                    location_index))

        return inserted

    def identify_and_init_thing(self, _thing_type, location_index):
        thing = None

        if _thing_type == AmmoType:
            thing = AmmoType(_location=location_index)
        elif _thing_type == Hurdle:
            thing = Hurdle(_location=location_index)
        elif _thing_type == EnemyArmorAgent:
            thing = EnemyArmorAgent(_location=location_index)
        elif _thing_type == BattleTankAgent:
            thing = BattleTankAgent()

        return thing

    def crossHurdle(self, hurdle_index, agent):
        # TODO agent has to scan for the potential hurdle in the next block
        # TODO if there's a hurdle in next target block then take necessary action.
        # TODO if there's an enemy right after the hurdle, then destroy the hurdle then shoot the enemy
        if agent.location < hurdle_index:
            # cross the hurdle and move to the right
            pass
        else:
            # cross the hurdle and move to the left
            pass

    def destroyHurdle(self, agent, location_index, ammo_type=AmmoType()):
        # when destroyed a hurdle, move in that block as next target position
        items_at_location = self.get_existing_items_at(location_index)

        hurdle = None
        if len(items_at_location) > 0:
            hurdle = items_at_location[0]

        for potential_hurdle in items_at_location:
            if isinstance(potential_hurdle, Hurdle):
                hurdle = potential_hurdle
                break

        old_health = hurdle.health
        # new_heal

        ammo_strength = ammo_type.get_ammo_strength()
        new_health = max(0, old_health - ammo_strength)

        hurdle.health = new_health
        damage_dealt = new_health - old_health

        print(hurdle.get_stats() + " dealt %d damage" % damage_dealt + " from %s" % agent.get_stats())

        if not hurdle.is_alive():
            self.remove_item_at(location_index, hurdle)
            print(hurdle.get_stats() + " was destroyed by %s " % agent.get_stats())
            self.relocate_agent(agent, location_index)

    def shootEnemy(self, source_agent, location_index, ammo_type=AmmoType()):
        items_at_location = self.get_existing_items_at(location_index)
        ammo_damage = ammo_type.get_ammo_strength()

        enemy = None
        if len(items_at_location) > 0:
            enemy = items_at_location[0]

        for item in items_at_location:
            if isinstance(item, ArmoredVehicleAgent):
                enemy = item
                break

        old_health = enemy.health

        new_health = max(0, old_health - ammo_damage)

        # update enemy health
        enemy.health = new_health

        # as damage dealt is negative, add this to the global enemy health
        damage_dealt = new_health - old_health

        # identify team and reduce global health of that team
        team = enemy.team
        if team == "1":
            self.global_good_players_total_health += damage_dealt
        elif team == "2":
            self.global_enemies_total_health += damage_dealt

        print(enemy.get_stats() + " took %d damage" % -damage_dealt + " from %s " % source_agent.get_stats())

        # if enemy agent is dead, remove it from the location and the respective team's list
        if not enemy.is_alive():
            self.remove_item_at(target_location=location_index, item=enemy)
            print(enemy.get_stats() + " died")

        self.actionHappened()

    def get_existing_items_at(self, location_index):
        existing_items_list = []

        if location_index in self.items_dictionary:
            existing_items_list = self.items_dictionary[location_index]

        # return existing_items as list in any situation so that adding hurdles and enemies directly to the location becomes easy
        if not isinstance(existing_items_list, list):
            existing_items_list = list()

        return existing_items_list

    def stockAmmo(self, agent):
        ammo_instance = self.collect_item_at_location(agent.location, AmmoType)

        return ammo_instance

    def collect_item_at_location(self, agent_location, instance_type):
        item_instance = None
        for item in self.get_existing_items_at(agent_location):
            if isinstance(item, instance_type):
                item_instance = item
                break

        # ensure removal of ammo from current location
        self.remove_item_at(target_location=agent_location, item=item_instance)

        return item_instance

    def remove_item_at(self, target_location, item):
        items_list = self.get_existing_items_at(target_location)
        items_list.remove(item)

        self.update_location_availability(_location_index=target_location)
        team = None
        if isinstance(item, ArmoredVehicleAgent) and not item.is_alive():
            team = item.team

            if team == "1":
                self.good_players.remove(item)
            elif team == "2":
                self.enemies.remove(item)

    def isEnemyAlive(self):
        """
        Returns true if there are still enemies alive in this Environment
        Game should be won then
        :return:
        """
        return self.global_enemies_total_health > 0

    def isPlayerAlive(self):
        return self.global_good_players_total_health > 0

    def initEnvironment(self):
        # TODO automate initEnvironment parameters using configuration file
        # insert players, hurdles, ammo and enem(y)/(ies)
        player_tank_agent = BattleTankAgent(_range=2, _health=1, _location=0)

        self.insert_generic_thing(_thing=player_tank_agent)
        # self.insert_generic_thing(_thing_type=EnemyArmorAgent)
        # self.insert_generic_thing(_thing=EnemyArmorAgent(_range=3))
        self.insert_generic_thing(_thing_type=EnemyArmorAgent)
        # self.insert_generic_thing(_thing_type=EnemyArmorAgent)
        # self.insert_generic_thing(_thing_type=EnemyArmorAgent)
        # self.insert_generic_thing(_thing_type=EnemyArmorAgent)
        # self.insert_generic_thing(_thing_type=EnemyArmorAgent)
        # self.insert_generic_thing(_thing_type=EnemyArmorAgent)
        # self.insert_generic_thing(_thing_type=EnemyArmorAgent)
        # self.insert_generic_thing(_thing_type=EnemyArmorAgent)
        # self.insert_generic_thing(_thing_type=EnemyArmorAgent)
        # self.insert_generic_thing(_thing_type=BattleTankAgent)
        # self.insert_generic_thing(_thing_type=BattleTankAgent)
        # self.insert_generic_thing(_thing_type=BattleTankAgent)
        # self.insert_generic_thing(_thing_type=BattleTankAgent)
        # self.insert_generic_thing(_thing_type=BattleTankAgent)
        # self.insert_generic_thing(_thing_type=Hurdle)
        # self.insert_generic_thing(_thing_type=Hurdle)
        # self.insert_generic_thing(_thing=Hurdle(_health=1))
        # self.insert_generic_thing(_thing=Hurdle(_health=1))
        # self.insert_generic_thing(_thing=Hurdle(_health=1))
        # self.insert_generic_thing(_thing_type=Hurdle)
        # self.insert_generic_thing(_thing_type=Hurdle)
        # self.insert_generic_thing(_thing_type=Hurdle)
        # self.insert_generic_thing(_thing_type=EnemyArmorAgent)
        # self.insert_generic_thing(_thing_type=EnemyArmorAgent)
        # self.insert_generic_thing(_thing_type=EnemyArmorAgent)
        # self.insert_generic_thing(_thing_type=Hurdle)
        # self.insert_generic_thing(_thing_type=Hurdle)
        # self.insert_generic_thing(_thing_type=Hurdle)
        # self.insert_generic_thing(_thing_type=EnemyArmorAgent)
        # self.insert_generic_thing(_thing_type=EnemyArmorAgent)
        # self.insert_generic_thing(_thing_type=AmmoType)
        # self.insert_generic_thing(_thing_type=AmmoType)
        # self.insert_generic_thing(_thing_type=AmmoType)
        # self.insert_generic_thing(_thing_type=AmmoType)
        # self.insert_generic_thing(_thing_type=AmmoType)
        # self.insert_generic_thing(_thing_type=AmmoType)
        # self.insert_generic_thing(_thing_type=AmmoType)
        # self.insert_generic_thing(_thing_type=AmmoType)
        # self.insert_generic_thing(_thing_type=AmmoType)
        # self.insert_generic_thing(_thing_type=AmmoType)
        # self.insert_generic_thing(_thing_type=AmmoType)
        # self.insert_generic_thing(_thing_type=AmmoType)
        # self.insert_generic_thing(_thing_type=AmmoType)
        # self.insert_generic_thing(_thing_type=AmmoType)
        # self.insert_generic_thing(_thing_type=AmmoType)
        # self.insert_generic_thing(_thing_type=AmmoType)
        # self.insert_generic_thing(_thing_type=AmmoType)
        # self.insert_generic_thing(_thing_type=AmmoType)
        # self.insert_generic_thing(_thing_type=AmmoType)
        # self.insert_generic_thing(_thing_type=Hurdle)
        # self.insert_generic_thing(_thing_type=Hurdle)
        # self.insert_generic_thing(_thing_type=Hurdle)
        # self.insert_generic_thing(_thing_type=EnemyArmorAgent)
        # self.insert_generic_thing(_thing=player_tank_agent)
        # self.insert_generic_thing(_thing_type=EnemyArmorAgent)
        # self.insert_generic_thing(_thing=player_tank_agent)
        # self.insert_generic_thing(_thing_type=Hurdle)
        # self.insert_generic_thing(_thing_type=Hurdle)
        # self.insert_generic_thing(_thing_type=Hurdle)
        # self.insert_generic_thing(_thing_type=Hurdle)
        # self.insert_generic_thing(_thing_type=EnemyArmorAgent)
        # self.insert_generic_thing(_thing=player_tank_agent)
        # self.insert_generic_thing(_thing_type=EnemyArmorAgent)
        # self.insert_generic_thing(_thing=player_tank_agent)

    def offerPlayerTurn(self):
        self.represent_this_world()

        # always offer good-player(BattleTankAgent) a first chance to perform actions,
        # this will ensure player doesn't get attacked even if it lands next to the enemy
        if self.good_player_turn:
            # pick random good player from good players list
            good_player_agent = random.choice(self.good_players)
            # player = ArmoredVehicleAgent()
            good_player_agent.play_a_move(environment=self)
            self.good_player_turn = not self.good_player_turn
        else:
            self.good_player_turn = not self.good_player_turn

            # pick enemy player
            enemy_agent = random.choice(self.enemies)
            enemy_agent.play_a_move(environment=self)

    def represent_this_world(self):
        # iterate over all locations and respective items at locations in items dictionary
        location_items_strings_dict = {}
        for i in range(0, self.battlefield.shape[0] + 1):
            location_item_string = ""
            if i in self.items_dictionary:
                item_list = self.items_dictionary[i]
                for item in item_list:
                    location_item_string += "%s," % item.get_char_string()

            location_items_strings_dict[i] = " %s " % location_item_string
            # +2 considering colspan

        target_line = ""
        target_index_line = ""
        for i in range(0, self.battlefield.shape[0] + 1):
            target_line += " %s |" % location_items_strings_dict[i]
            target_index_line += " %d" % i + (" " * len(location_items_strings_dict[i])) + "|"

        chars_count = len(target_line)

        # draw overline
        print("+%s+" % ("-" * chars_count))
        print("| %s " % target_index_line)
        print("| %s " % target_line)

        # draw underline
        print("+%s+" % ("-" * chars_count))

    def game_finished(self):
        x, y = self.analyzeWinCondition()

        game_finished = x or y

        return game_finished

    def analyzeWinCondition(self):
        good_player_won = (self.global_good_players_total_health > 0) and (self.global_enemies_total_health <= 0)
        good_player_lost = (self.global_enemies_total_health > 0) and (self.global_good_players_total_health <= 0)

        return good_player_won, good_player_lost
