from __future__ import annotations
from typing import TYPE_CHECKING

from models import Player, CityState
from eng import db

if TYPE_CHECKING:
    from data.cities import CityGame, CityGraph


class PlayerGame:
    def __init__(self, game, id: int, name: str, role_id: int, pos: CityGame | None):
        self.game = game
        self.id = id
        self.name = name
        self.role_id = role_id
        self.pos = pos
        self.actions_left = 4
    
    def from_db(self, player_db: Player, city_graph):
        self.id = player_db.id
        self.name = player_db.name
        self.role_id = player_db.role_id
        
        city_state = CityState.query.get(player_db.position_city_id)
        base_city = city_state.base_city
        self.pos = city_graph.get_city_by_name(base_city.name)
        self.pos.players.append(self)
        
        self.actions_left = player_db.actions_left
        
        return self
    
    def to_db(self, player_db: Player):
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
        pg.from_db(pl, game.cities)
        players.append(pg)
    return players
