from collections import OrderedDict

import numpy as np

from constants.AmmoTypes import AmmoType
from constants.KnowledgeBaseItemConstants import KRConstants
from constants.Moves import Moves
from environment.entities.EnvironmentEntity import EnvironmentEntity
from environment.entities.Hurdle import Hurdle
import random

class ArmoredVehicleAgent(EnvironmentEntity):
    """
        :author: Aniruddha Kalburgi
        """

    def __init__(self, _location, _range, _health=1, _elite_ammo_count=0, _name="ArmoredVehicleAgent", _team="1",
                 char_string="UKN_T"):
        super().__init__(_location, _health, _name=_name, _is_static=False, _char_string=char_string)
        # the range for Player's bot agent has to be 2 or higher, otherwise entering enemy range of 1 makes player-agent susceptible to get shot by the enemy-agent

        # in knowledge base - health history and static items subdictionaries separate per location
        self.knowledge_base = {}
        self.is_static = False
        self.range = _range
        self.actions_pool = list()
        self.elite_ammo_dict = {}
        self.environment = None
        self.item_locations_dictionary = {}
        self.team = _team

    def play_a_move(self, environment):
        self.environment = environment
        # analyze
        # take decision- # whether to move,
        # collect ammo,
        # destroy/pass the hurdle
        # or shoot enemy

        # perceive
        at_current_location, items_within_range = environment.perceive(self)

        # update knowledge-base
        self.update_knowledge_base(in_range_items=items_within_range)

        # consume ammo at current location if available
        if len(at_current_location) > 1:
            for item in at_current_location:
                # consume ammo at current location
                if isinstance(item, AmmoType):
                    ammo = environment.stockAmmo(self)
                    self.add_elite_ammo(ammo)

        if len(items_within_range) > 0:
            target_path, priorities = self.calculate_target_path_and_priorities(in_range=items_within_range)

            action = None
            location = None
            if not priorities is None:
                action, location = self.get_next_action_and_location(target_path, priorities)
                if self.environment.battlefield.shape.__len__() > 1 and len(location) > 1:
                    location = tuple(location)

            self.perform_action(action, location)
        else:
            self.make_knowledge_based_move()
        # TODO remove print or replace with best alternative
        print("Agent action completed\n")

    def update_knowledge_base(self, in_range_items):
        # knowledge base is updated for every single location in every single chance
        # in knowledge base - health history and static items sub-dictionaries separate per location

        health_history = []
        static_items = []

        # init or get existing knowledge dictionaries
        if self.location not in self.knowledge_base:
            # sub-dictionary of health history and static-objects
            sub_dictionary = {KRConstants.HEALTH_HISTORY: list(), KRConstants.STATIC_OBJECTS: list()}

            # sub-dictionaries records kept per location
            self.knowledge_base[self.location] = sub_dictionary
        else:
            if len(self.knowledge_base[self.location]) > 0:
                health_history = self.knowledge_base[self.location][KRConstants.HEALTH_HISTORY]
                static_items = self.knowledge_base[self.location][KRConstants.STATIC_OBJECTS]

        # add to current knowledge if static objects found in_range
        for item in in_range_items:
            if item.is_static_entity():
                # don't add redudant static items
                if item not in static_items:
                    static_items.append(item)

        # for health, add redundant instances as well
        health_history.append(self.health)

        # Update list in the knowledge-base
        self.knowledge_base[self.location][KRConstants.HEALTH_HISTORY] = health_history
        self.knowledge_base[self.location][KRConstants.STATIC_OBJECTS] = static_items

    def get_stats(self):
        return super().get_stats() + ", range:%d" % self.range + ", team:%s" % self.team

    def add_elite_ammo(self, ammo_instance):
        ammo_type_name = ammo_instance.name
        ammo_count = 0

        if ammo_type_name in self.elite_ammo_dict:
            ammo_count = self.elite_ammo_dict[ammo_type_name]

        ammo_count += ammo_instance.get_ammo_count()

        self.elite_ammo_dict[ammo_instance.name] = ammo_count

    def make_knowledge_based_move(self):
        target_location = None

        # Prioritize unexplored nearest positions based on knowledge in knowledge-base
        explored, unexplored = self.prioritize_positions_using_knowledge_base()

        if len(unexplored) > 0:
            # if there exists unexplored positions then make random choice between them and visit one
            print("Prioritizing unexplored location as target location")
            if self.environment.battlefield.shape.__len__() == 1:
                target_location = np.random.choice(np.array(unexplored))
            else:
                target_location = random.choice(unexplored)
        else:
            print(
                "Prioritizing highest profit location : profit = (target_location_items_priority - health damage dealt in past at the location)")
            # make use of existing health-based history and static-items data
            # prepare profit_minus_risk{} dictionary, and choose target_location with least risk and more profit
            profit_minus_risk = {}

            # for items in KBPresentList
            for position in explored:
                potential_profit = 0
                health_history = self.knowledge_base[position][KRConstants.HEALTH_HISTORY]

                # check health difference between last item and first item
                damage_risk = health_history[0] - health_history[-1]
                potential_profit -= damage_risk

                # also present in static items
                static_items = self.knowledge_base[position][KRConstants.STATIC_OBJECTS]
                if len(static_items) > 0:
                    # get priority of static items for all possible positions that are present in KB
                    for item in static_items:
                        priority = self.get_item_priority(item)
                        potential_profit += priority

                profit_minus_risk[position] = potential_profit

            # finally you have locations with most to least potential profits
            # choose the one with highest or random in case of tie
            most_profitable = []
            # -100,000 in case profit goes in negative when just health was damaged at location
            highest_profit = -100000

            for location in profit_minus_risk.keys():
                if highest_profit < profit_minus_risk[location]:
                    highest_profit = profit_minus_risk[location]
                    most_profitable.append(location)

            if len(most_profitable) > 0:
                if self.environment.battlefield.shape.__len__() > 1:
                    target_location = random.choice(most_profitable)
                else:
                    target_location = np.random.choice(most_profitable)

        if not (target_location is None):
            action = Moves.MOVE_TO_THE_TARGET
            self.perform_action(action=action, location=target_location)

    def prioritize_positions_using_knowledge_base(self):
        # start with scanning possible moves in free world
        possible_movement_positions = self.list_possible_movements()
        unexplored_positions = []
        explored_positions = []

        # make list of positions not present in knowledge base
        for possible_position in possible_movement_positions:
            if possible_position in self.knowledge_base:
                health_history_length = len(self.knowledge_base[possible_position][KRConstants.HEALTH_HISTORY])
                static_objects_length = len(self.knowledge_base[possible_position][KRConstants.STATIC_OBJECTS])

                if static_objects_length == 0 and health_history_length == 0:
                    unexplored_positions.append(possible_position)
                else:
                    explored_positions.append(possible_position)
            else:
                unexplored_positions.append(possible_position)

        return explored_positions, unexplored_positions

    def list_possible_movements(self):
        possible_movements = []

        # get environment properties - min and max range
        environment_shape = self.environment.battlefield.shape

        if environment_shape.__len__() == 1:
            max_value = environment_shape[0] - 1

            possible_left_move = max(0, self.location - 1)
            if possible_left_move != self.location:
                possible_movements.append(possible_left_move)

            possible_right_move = min(max_value, self.location + 1)
            if possible_right_move != self.location:
                possible_movements.append(possible_right_move)
        else:
            # considering environment is 2D
            possible_movements = self.list_possible_2d_movements()

        return possible_movements

    def list_possible_2d_movements(self):
        # create tuple of all nearby indices and then subtract those out of range
        all_movements = []
        loc_row, loc_col = self.location

        # list all possibilities including out of bound locations
        for i in range(loc_row - 1, loc_row + 2):
            for j in range(loc_col - 1, loc_col + 2):
                the_tuple = (i, j)
                if the_tuple != self.location:
                    all_movements.append((i, j))

        # remove out of bound
        possible_movements_np = np.array(all_movements)
        row = possible_movements_np[:, 0]
        column = possible_movements_np[:, 1]

        field_width = self.environment.fieldWidth - 1
        field_height = self.environment.fieldHeight - 1

        row_comparison_bool = np.logical_and(np.greater_equal(row, 0), np.greater_equal(column, 0))
        col_comparison_bool = np.logical_and(np.less_equal(row, field_width), np.less_equal(column, field_height))
        bool_comp_result = np.logical_and(row_comparison_bool, col_comparison_bool)

        possible_movements = []
        i = 0
        # Couldn't use enumerate or ndenumerate as there are tuples in the list
        for tuple_element in all_movements:
            if bool_comp_result[i]:
                if bool_comp_result[i]:
                    possible_movements.append((tuple_element[0], tuple_element[1]))
            i += 1

        return possible_movements

    def perform_action(self, action, location):
        if action is Moves.SHOOT:
            # call shoot method from environment
            # TODO choose ammo-type and equip elite if available
            # shootEnemy(self, location_index, ammo_type=AmmoType.TANK_BULLETS)
            self.environment.shootEnemy(self, location)
        elif action is Moves.SHOOT_HURDLE:
            self.environment.destroyHurdle(self, location)
        elif action is Moves.MOVE_TO_THE_TARGET:
            self.environment.relocate_agent(self, location)
        else:
            print("making knowledge based move despite things in range")
            self.make_knowledge_based_move()

    def equip_right_ammo(self):
        # TODO if elite ammo is available, equip best elite ammo
        pass

    def get_next_action_and_location(self, target_path, priorities):
        priorities = np.array(priorities)
        target_path = np.array(target_path)
        sorted_priorities = np.argsort(-priorities)
        next_action = None

        target_location = target_path[sorted_priorities][0]

        if self.environment.battlefield.shape.__len__() > 1 and len(target_location) > 1:
            target_location = (target_location[0], target_location[1])

        things = self.item_locations_dictionary[target_location]

        # choose top priority target from the list of items at target location
        thing_priority = 0
        target = things[0]
        for thing in things:
            new_priority = self.get_item_priority(thing)
            if new_priority > thing_priority:
                target = thing

        if isinstance(target, Hurdle):
            next_action = Moves.SHOOT_HURDLE
        elif self.is_enemy(target):
            next_action = Moves.SHOOT
        elif isinstance(target, AmmoType):
            next_action = Moves.MOVE_TO_THE_TARGET
            # not directly to the ammo location but move to the closer location
            # TODO test this carefully
            target_location = target_path[0]

        return next_action, target_location

    def is_enemy(self, thing):
        if isinstance(thing, ArmoredVehicleAgent):
            return self.team != thing.team
        return False

    def calculate_target_path_and_priorities(self, in_range):
        # creating item-location dictionary
        locations = self.get_in_range_locations_list(
            in_range)  # TODO remove this as it is unused, also remove the method if not used anywhere
        self.item_locations_dictionary = self.create_item_locations_dictionary(in_range, locations)

        priorities = []
        location_visited = []
        for item in in_range:
            # only append priority for highest priority element from that location, i.e. 1 priority per location
            # priorities.append(self.get_item_priority(target_item=item))
            if item.location not in location_visited:
                priorities.append(self.get_most_valuable_item_priority(item.location))
                location_visited.append(item.location)

        priorities = np.array(priorities)
        sorted_priorities = (np.argsort(-priorities))

        target_path, new_priorities = self.create_chain(in_range=in_range, priorities=priorities,
                                                        sorted_priorities=sorted_priorities,
                                                        locations=locations)

        return target_path, new_priorities

    def create_chain(self, in_range, priorities, sorted_priorities, locations):
        target = in_range[sorted_priorities[0]]

        target_path = self.identify_initial_target_path(in_range=in_range, priorities=priorities,
                                                        sorted_priorities=sorted_priorities, target=target,
                                                        locations=locations)
        new_priorities = self.identify_chain_items_and_recalculate_priorities(target_path=target_path, _target=target)

        return target_path, new_priorities

    def get_item_priority(self, target_item):
        return self.environment.priorities.getPriorityForThing(self, target_thing=target_item).value

    def get_most_valuable_item_priority(self, location_index):
        existing_items = []

        if location_index in self.item_locations_dictionary:
            existing_items = self.item_locations_dictionary[location_index]

        priority = 0
        for item in existing_items:
            new_priority = self.get_item_priority(item)
            if new_priority > priority:
                priority = new_priority

        return priority

    def identify_chain_items_and_recalculate_priorities(self, target_path, _target):
        new_priorities = []
        enemy_detected = False

        for next_location in target_path:
            # if something crashes here with key-error, probably there's an error in creating target_paths
            # TODO if error isn't fixed, return blank list of priorities and see what happens, or else append 0 to empty priority list and return it
            if next_location in self.item_locations_dictionary:
                items = self.item_locations_dictionary[next_location]

                visited = []
                new_priority = 0
                for item in items:
                    # get priority of most valuable item
                    if item.location not in visited:
                        # new_priority = self.get_item_priority(target_item=item)
                        new_priority = self.get_most_valuable_item_priority(item.location)
                        visited.append(item.location)

                        if isinstance(item, Hurdle) and not enemy_detected:
                            target_priority = self.get_item_priority(target_item=_target)
                            new_priority += target_priority
                        elif new_priority == 10 and not enemy_detected:
                            # the enemy
                            enemy_detected = True

                        new_priorities.append(new_priority)
            else:
                return

        return new_priorities

    def create_item_locations_dictionary(self, in_range, locations):
        item_locations_dictionary = {}

        for item in in_range:
            new_items = []
            if item.location in item_locations_dictionary:
                new_items = item_locations_dictionary[item.location]

            new_items.append(item)
            item_locations_dictionary[item.location] = new_items

        return item_locations_dictionary

    def get_in_range_locations_list(self, in_range):
        locations = []

        for item in in_range:
            locations.append(item.location)

        return np.array(locations)

    def identify_initial_target_path(self, in_range, priorities, sorted_priorities, target, locations):
        target_path = []
        # 1D
        # if target.location.shape.__len__() == 0:
        if self.environment.battlefield.shape.__len__() == 1:
            if target.location < self.location:
                # backward chain
                target_path.extend(locations[locations < self.location][::-1])
            else:
                # forward chain
                target_path.extend(locations[locations > self.location])

            target_path = list(OrderedDict.fromkeys(target_path))
        else:
            # TODO 2D
            # Diagonal or row or column
            difference_tuple = np.subtract(self.location, target.location)

            difference_x = difference_tuple[0]
            difference_y = difference_tuple[1]

            agent_x = self.location[0]
            agent_y = self.location[1]

            # difference_absolute
            difference_absolute = tuple(np.abs(difference_tuple))
            absolute_x = difference_absolute[0]
            absolute_y = difference_absolute[1]

            target_x = target.location[0]
            target_y = target.location[1]

            # diagonal
            if absolute_x == absolute_y:
                # find diagonal path to target
                target_path = self.get_diagonal_path(agent_x, agent_y, difference_x, difference_y, target_x, target_y)
            elif difference_x == 0 or difference_y == 0:
                target_path = self.get_horizontal_or_vertical_path(agent_x, agent_y, difference_x, difference_y,
                                                                   target_x, target_y)
            else:
                target1_location = (agent_x, target_y)

                target1_x = target1_location[0]
                target1_y = target1_location[1]

                target1_difference = np.subtract(self.location, target1_location)
                t1_difference_x = target1_difference[0]
                t1_difference_y = target1_difference[1]

                path1 = self.get_horizontal_or_vertical_path(agent_x, agent_y, t1_difference_x, t1_difference_y,
                                                             target1_x,
                                                             target1_y)

                target1_to_target_difference = np.subtract((target1_x, target1_y), target.location)
                difference_x = target1_to_target_difference[0]
                difference_y = target1_to_target_difference[1]
                path2 = self.get_horizontal_or_vertical_path(target1_x, target1_y, difference_x, difference_y, target_x,
                                                             target_y)

                target_path.extend(path1)
                target_path.extend(path2)

        return target_path

    def get_horizontal_or_vertical_path(self, agent_x, agent_y, difference_x, difference_y, target_x, target_y):
        arr1 = []
        arr2 = []

        if difference_y == 0:
            if difference_x > 0:
                arr1 = np.arange(agent_x - 1, target_x - 1, -1)
                arr2 = np.array([agent_y] * len(arr1))
            elif difference_x < 0:
                arr1 = np.arange(agent_x + 1, target_x + 1, 1)
                arr2 = np.array([agent_y] * len(arr1))
        elif difference_x == 0:
            if difference_y > 0:
                arr2 = np.arange(agent_y - 1, target_y - 1, -1)
                arr1 = np.array([agent_x] * len(arr2))
            elif difference_y < 0:
                arr2 = np.arange(agent_y + 1, target_y + 1, 1)
                arr1 = np.array([agent_x] * len(arr2))

        target_path = tuple(zip(arr1, arr2))
        return target_path

    def get_diagonal_path(self, agent_x, agent_y, difference_x, difference_y, target_x, target_y):
        arr1 = []
        arr2 = []

        if difference_x > 0:
            if difference_y > 0:
                arr1 = np.arange(agent_x - 1, target_x - 1, -1)
                arr2 = np.arange(agent_y - 1, target_y - 1, -1)
            else:
                arr1 = np.arange(agent_x - 1, target_x - 1, -1)
                arr2 = np.arange(agent_y + 1, target_y + 1, 1)
        elif difference_x < 0:
            if difference_y < 0:
                arr1 = np.arange(agent_x + 1, target_x + 1, 1)
                arr2 = np.arange(agent_y + 1, target_y + 1, 1)
            else:
                arr1 = np.arange(agent_x + 1, target_x + 1, 1)
                arr2 = np.arange(agent_y - 1, target_y - 1, -1)

        path_locations = tuple(zip(arr1, arr2))

        return path_locations
