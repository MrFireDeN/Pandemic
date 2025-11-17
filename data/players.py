from __future__ import annotations
from typing import TYPE_CHECKING

from models import Player, CityState, City, ColorEnum, CardType
from eng import db

if TYPE_CHECKING:
    from data.cities import CityGame, CityGraph
    from data.decks import CardGame, DeckCards


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

    def move_by_car(self, is_fair=True):
        pass

    def move_by_direct_flight(self):
        pass

    def move_by_charter_flight(self):
        pass

    def move_by_research_flight(self):
        pass

    def build_research_station(self):
        pass

    def cure_disease(self):
        pass

    def trade_card(self, card: CardGame, with_player: PlayerGame, give_or_apply: bool = True):
        pass

    def apply_card(self, card: CardGame):
        pass

    def give_card(self, card: CardGame, player: PlayerGame):
        pass

    def make_vaccine(self, color: str | ColorEnum, cards: list[CardGame]):
        pass

    def log_action(self, is_fair: bool = True):
        pass
    
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
