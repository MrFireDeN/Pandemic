from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from data.enums import RoleType, ColorType
    from data.cities import CityGame
    from data.decks import CardGame


class PlayerGame:
    def __init__(self, game, player_id: int, name: str, role_id: int, pos: CityGame | None):
        self.game = game
        self.id = player_id
        self.name = name
        self.role = RoleType[role_id]
        self.pos = pos
        self.actions_left = 4

    def move_to(self, city: CityGame, use_card: CardGame | None = None):
        city_from = self.pos
        city_to = city

        is_research_flight = city_from.has_station and city_to.has_station

        if is_research_flight:
            self.__move_by_research_flight(city_to)
            return

        is_by_car = city_to in city_from.connections

        if is_by_car:
            self.__move_by_car(city_to)
            return

        if use_card is not None and use_card.is_city():
            if use_card.name == city_from.name:
                self.__move_by_charter_flight(city)
                return

            if use_card.name == city_to.name:
                self.__move_by_direct_flight(city_to)
                return

        self.__move_by_cheat(city_to)

    def build_research_station(self, city: CityGame, card: CardGame | None = None):
        # graph = city.graph

        if self.role == RoleType.ENGINEER:
            city.graph.build_research_station(city.name)
            self.__commit_action()
            return

        if card is not None:
            city.graph.build_research_station(city.name)
            # TODO: card
            self.__commit_action()
            return

    def cure_city(self, city: CityGame, color: str | ColorType):
        if isinstance(color, ColorType):
            color = color.name

        count = 3 if self.role == RoleType.DOCTOR else 1
        city.remove_infection(color, count)
        self.__commit_action()
        return

    def discover_cure(self, color: str | ColorType, cards: list[CardGame]):
        if isinstance(color, ColorType):
            color = color.name

        # TODO
        count_color = len(cards)
        if self.role == RoleType.SCIENTIST:
            count_color += 1

        if count_color >= 5:
            self.game.board.cure_discovered(color)
            self.__commit_action()


    def trade_card(self, card: CardGame, with_player: PlayerGame, give_or_apply: bool = True):
        pass

    def serialize(self):
        pass

    def deserialize(self):
        pass

    def __move_by_car(self, city: CityGame):
        self.pos = city
        self.__commit_action()

    def __move_by_direct_flight(self, city: CityGame):
        self.pos = city
        self.__commit_action()

    def __move_by_charter_flight(self, city: CityGame):
        self.pos = city
        self.__commit_action()

    def __move_by_research_flight(self, city: CityGame):
        self.pos = city
        self.__commit_action()
        
    def __move_by_cheat(self, city: CityGame):
        self.pos = city
        self.__commit_action(is_fair=False)

    def __apply_card(self, card: CardGame):
        pass

    def __give_card(self, card: CardGame, player: PlayerGame):
        pass

    def __commit_action(self, text: str | None = None, is_fair: bool = True):
        self.actions_left -= 1

        if self.actions_left <= 0:
            self.game.notify_turn_ended()

        if is_fair:
            print(f'{self.name} {text}')
        else:
            print(f'cheating: {self.name} {text}')
