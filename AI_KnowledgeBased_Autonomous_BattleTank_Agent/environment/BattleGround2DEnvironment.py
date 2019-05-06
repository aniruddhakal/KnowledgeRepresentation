import random

import numpy as np

from constants.AmmoTypes import AmmoType
from environment.BattleGroundEnvironment import BattleGround
from environment.entities.Hurdle import Hurdle
from environment.entities.agents.ArmoredVehicleAgent import ArmoredVehicleAgent
from environment.entities.agents.BattleTankAgent import BattleTankAgent
from environment.entities.agents.EnemyArmorAgent import EnemyArmorAgent
from constants.Priorities import Priorities


# class BattleGround2DEnvironment(BattleGround):
class BattleGround2DEnvironment:
    """
        :author: Aniruddha Kalburgi
        """

    # TODO redefine
    def __init__(self, _field_width=10, _field_height=5):
        # changed
        # super().__init__()
        # TODO redefine
        self.fieldWidth = _field_width
        self.fieldHeight = _field_height
        # TODO redefine
        self.battlefield = np.zeros((self.fieldWidth, self.fieldHeight), dtype=np.uint32)
        self.items_dictionary = {}
        self.enemies = list()
        self.global_enemies_total_health = 0
        self.good_players = list()
        self.global_good_players_total_health = 0
        self.good_player_turn = True
        self.priorities = Priorities

    def perceive(self, agent):
        # changed
        # TODO redefine
        """
        :return tuple (items at current location, array of items in range - but not at current location)
        """
        items_at_location = self.get_existing_items_at(agent.location)

        items_in_range = list()

        items_in_range.extend(self.perceive_items_within_range(agent))

        return items_at_location, items_in_range

    def list_possible_2d_movements(self, agent_location, agent_range):
        # create tuple of all nearby indices and then subtract those out of range
        all_movements = []
        loc_row, loc_col = agent_location

        # list all possibilities including out of bound locations
        for i in range(loc_row - agent_range, loc_row + agent_range + 1):
            for j in range(loc_col - agent_range, loc_col + agent_range + 1):
                the_tuple = (i, j)
                if the_tuple != agent_location:
                    all_movements.append((i, j))

        # remove out of bound
        possible_movements_np = np.array(all_movements)
        row = possible_movements_np[:, 0]
        column = possible_movements_np[:, 1]

        field_width = self.fieldWidth - 1
        field_height = self.fieldHeight - 1

        row_comparison_bool = np.logical_and(np.greater_equal(row, 0), np.greater_equal(column, 0))
        col_comparison_bool = np.logical_and(np.less_equal(row, field_width), np.less_equal(column, field_height))
        bool_comp_result = np.logical_and(row_comparison_bool, col_comparison_bool)

        possible_movements = []
        i = 0
        for tuple_element in all_movements:
            if bool_comp_result[i]:
                if bool_comp_result[i]:
                    possible_movements.append((tuple_element[0], tuple_element[1]))
            i += 1

        return possible_movements

    def perceive_items_within_range(self, agent):
        perceived_items = []

        in_range_locations = self.list_possible_2d_movements(agent.location, agent.range)

        for location in in_range_locations:
            if location in self.items_dictionary:
                perceived_items.extend(self.items_dictionary[location])

        return perceived_items

    def actionHappened(self):
        # TODO called when something is inserted, health updated, destroyed/killed etc
        # identify more events for actionHappened()
        # TODO each time this function is called, trigger change representation method and paint the current world state
        pass

    def get_random_available_location(self):
        random_location = -1

        if len(self.battlefield.shape) > 1:
            random_location = (-1, -1)

        rows, columns = np.where(self.battlefield == 0)
        available_indices = tuple(zip(rows, columns))

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

        if not isinstance(_location_index, tuple) and self.battlefield.shape.__len__() > 1:
            _location_index = tuple(_location_index)

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
        # changed
        if _thing is None and _thing_type is None:
            print("Please pass valid argument to insert_generic_thing(_thing or _target_method) method")
            return False

        inserted = False
        location_index = self.get_random_available_location()

        if _thing is None:
            _thing = self.identify_and_init_thing(_thing_type=_thing_type, location_index=location_index)

        # if location_index == (-1, -1) and isinstance(_thing, AmmoType):
        if len(location_index) == 0 and isinstance(_thing, AmmoType):
            # this is for 1D array :      location_index = random.choice([x for x in range(0, len(self.battlefield))])
            # choose any location for ammo as it can be inserted almost everywhere
            rows, columns = np.where(self.battlefield == self.battlefield)
            available_indices = tuple(zip(rows, columns))

            if len(available_indices) > 0:
                location_index = random.choice(available_indices)
        elif location_index == (-1, -1):
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

        if not isinstance(location_index, tuple) and self.battlefield.shape.__len__() > 1:
            # print("Location %s isn't tuple" %str(location_index))
            location_index = tuple(location_index)

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
        player_tank_agent = BattleTankAgent(_range=6, _health=5, _location=0)

        self.insert_generic_thing(_thing=player_tank_agent)
        self.insert_generic_thing(_thing_type=EnemyArmorAgent)
        self.insert_generic_thing(_thing=EnemyArmorAgent(_range=3))
        self.insert_generic_thing(_thing_type=EnemyArmorAgent)
        self.insert_generic_thing(_thing_type=EnemyArmorAgent)
        self.insert_generic_thing(_thing_type=BattleTankAgent)
        self.insert_generic_thing(_thing_type=BattleTankAgent)
        self.insert_generic_thing(_thing_type=Hurdle)
        self.insert_generic_thing(_thing_type=Hurdle)
        self.insert_generic_thing(_thing_type=AmmoType)
        self.insert_generic_thing(_thing_type=AmmoType)
        self.insert_generic_thing(_thing_type=AmmoType)
        self.insert_generic_thing(_thing_type=AmmoType)
        self.insert_generic_thing(_thing_type=AmmoType)

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
        # generate 2D environment location tuples
        two_d_env_tuple_locations = []
        for i in range(0, self.fieldWidth):
            for j in range(0, self.fieldHeight):
                two_d_env_tuple_locations.append((i, j))

        # iterate over all locations and respective items at locations in items dictionary
        location_items_strings_dict = {}
        for location in two_d_env_tuple_locations:
            location_item_string = ""
            if location in self.items_dictionary:
                item_list = self.items_dictionary[location]
                for item in item_list:
                    location_item_string += "%s," % item.get_char_string()

            difference = int((16 - len(location_item_string)) / 2)
            location_items_strings_dict[location] = (" " * difference) + location_item_string + (" " * difference)
        # +2 considering colspan

        print("\nPLR_T: Good Player Tank, ENM_T: Enemy Tank, HUR: Hurdle, AMO: Ammo")
        index = -1
        print((("+%s" % ("-" * 16)) * self.fieldHeight) + "+")
        for i in range(0, self.fieldWidth):
            index += 1
            target_string = "|"
            for j in range(0, self.fieldHeight):
                target_string += location_items_strings_dict[(i, j)] + "|"

            print("%s" % target_string)
            print((("+%s" % ("-" * 16)) * self.fieldHeight) + "+")

    def game_finished(self):
        x, y = self.analyzeWinCondition()

        game_finished = x or y

        return game_finished

    def analyzeWinCondition(self):
        good_player_won = (self.global_good_players_total_health > 0) and (self.global_enemies_total_health <= 0)
        good_player_lost = (self.global_enemies_total_health > 0) and (self.global_good_players_total_health <= 0)

        return good_player_won, good_player_lost


def main():
    bg = BattleGround2DEnvironment(_field_width=10, _field_height=5)
    bg.initEnvironment() #add items in the world inside init function()

    while not bg.game_finished():
        bg.offerPlayerTurn()

    victory, loss = bg.analyzeWinCondition()
    if victory:
        print("\n\nGood Player Won\n")
    else:
        print("\n\nGood Player Lost\n")

    bg.represent_this_world()


if __name__ == '__main__':
    main()
