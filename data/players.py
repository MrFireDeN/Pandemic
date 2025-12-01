from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from models import Player, CityState, ColorEnum, CardType
from eng import db

if TYPE_CHECKING:
    from data.cities import CityGame, CityGraph
    from data.decks import CardGame, DeckCards


class RoleEnum(Enum):
    QUARANTINE_SPECIALIST = 1
    EMERGENCY_EXPERT = 2
    DISPATCHER = 3
    SCIENTIST = 4
    DOCTOR = 5
    RESEARCHER = 6
    ENGINEER = 7


class PlayerGame:
    def __init__(self, game, player_id: int, name: str, role_id: int, pos: CityGame | None):
        self.game = game
        self.id = player_id
        self.name = name
        self.role_id = role_id
        self.pos = pos
        self.actions_left = 4

    def move_to(self, city: CityGame, use_card: CardGame | None = None):
        city_from = self.pos
        city_to = city

        is_research_flight = city_from.has_station and city_to.has_station

        if is_research_flight:
            self.move_by_research_flight()
            return

        is_by_car = city_to in city_from.connections

        if is_by_car:
            self.move_by_car()
            return

        if use_card is not None and use_card.is_city():
            if use_card.name == city_from.name:
                self.move_by_charter_flight()
                return

            if use_card.name == city_to.name:
                self.move_by_direct_flight()
                return

        self.move_by_car(is_fair=False)

    def move_by_car(self, city: CityGame, is_fair=True):
        self.pos = city
        self.log_action(is_fair)

    def move_by_direct_flight(self, city: CityGame):
        self.pos = city
        self.log_action()

    def move_by_charter_flight(self, city: CityGame):
        self.pos = city
        self.log_action()

    def move_by_research_flight(self, city: CityGame):
        self.pos = city
        self.log_action()

    def build_research_station(self, city: CityGame, card: CardGame | None = None):
        graph = city.graph

        if self.role_id == RoleEnum.ENGINEER:
            city.graph.add_research_station(city.name)
            self.log_action()
            return

        if card is not None:
            city.graph.add_research_station(city.name)
            # TODO: card
            self.log_action()
            return


    def cure_disease(self, city: CityGame, color: str | ColorEnum):
        if isinstance(color, ColorEnum):
            color = color.value

        count = 3 if self.role_id == RoleEnum.DOCTOR else 1
        city.remove_infection(color, count)
        self.log_action()
        return

    def discover_cure(self, color: str | ColorEnum, cards: list[CardGame]):
        if isinstance(color, ColorEnum):
            color = color.value

        # TODO
        count_color = len(cards)
        if self.role_id == RoleEnum.SCIENTIST:
            count_color += 1

        if count_color >= 5:
            self.game.board.cure_discovered(color)
            self.log_action()


    def trade_card(self, card: CardGame, with_player: PlayerGame, give_or_apply: bool = True):
        pass

    def apply_card(self, card: CardGame):
        pass

    def give_card(self, card: CardGame, player: PlayerGame):
        pass

    def log_action(self, text: str | None = None, is_fair: bool = True):
        self.actions_left -= 1

        if self.actions_left <= 0:
            self.game.notify_turn_ended()

        if is_fair:
            print(f'{self.name} {text}')
        else:
            print(f'cheating: {self.name} {text}')
    
    def load_from_db(self, player_db: Player, city_graph):
        self.id = player_db.id
        self.name = player_db.name
        self.role_id = player_db.role_id
        
        city_state = CityState.query.get(player_db.position_city_id)
        base_city = city_state.base_city
        self.pos = city_graph.get_city_by_name(base_city.name)
        self.pos.players.append(self)
        
        self.actions_left = player_db.actions_left
        
        return self
    
    def save_to_db(self, player_db: Player):
        if player_db.actions_left == self.actions_left and player_db.position_city_id == self.pos.id:
            return
            
        player_db.position_city_id = self.pos.id
        player_db.actions_left = self.actions_left

        db.session.commit()


def load_players(game):
    rows = Player.query.filter_by(game_id=game.code).all()
    players = []
    for pl in rows:
        pg = PlayerGame(game, pl.id, pl.name, pl.role_id, None)
        pg.load_from_db(pl, game.cities)
        players.append(pg)
    return players
