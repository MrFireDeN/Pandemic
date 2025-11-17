from __future__ import annotations
from typing import TYPE_CHECKING

from models import City, CityConnection, CityState
from eng import db

if TYPE_CHECKING:
    from data.players import PlayerGame


class CityGame:
    def __init__(self, game, id: int, name: str, color: str):
        self.game = game
        self.id = id
        self.name = name
        self.color = color
        
        self.connections: list[CityGame] = []
        self.players: list[PlayerGame] = []
        
        self.has_station = False
        self.infection_cubes = {
            "red": 0,
            "yellow": 0,
            "blue": 0,
            "black": 0
        }

    def connect(self, other: CityGame):
        if other not in self.connections:
            self.connections.append(other)
            other.connections.append(self)
            
    def is_connected(self, other: CityGame) -> bool:
        return other in self.connections

    def add_infection(self, color: str, count: int = 1):
        self.infection_cubes[color] += count

    def remove_infection(self, color: str, count: int = 1):
        self.infection_cubes[color] = max(0, self.infection_cubes[color] - count)
        
    def load_from_db(self, city_db: CityState):
        city = city_db.base_city
        
        self.id = city.id
        self.name = city.name
        self.color = city.color.value
        
        self.has_station = city.has_station
        self.infection_cubes["blue"] = city.blue
        self.infection_cubes["yellow"] = city.yellow
        self.infection_cubes["black"] = city.black
        self.infection_cubes["red"] = city.red
        
        return self
    
    def save_to_db(self, city_db: CityState):
        city_db.has_station = self.has_station
        
        city_db.red = self.infection_cubes["red"]
        city_db.yellow = self.infection_cubes["yellow"]
        city_db.black = self.infection_cubes["black"]
        city_db.blue = self.infection_cubes["blue"]

        db.session.commit()


class CityGraph:
    def __init__(self, game):
        self.game = game
        self.cities_by_name: dict[str, CityGame] = {}
        self.cities_by_id: dict[int, CityGame] = {}
        
        self.start_city: str = 'Atlanta'

    def add_city(self, id: int, name: str, color: str):
        city = CityGame(self.game, id, name, color)
        self.cities_by_name[name] = city
        self.cities_by_id[id] = city

    def connect(self, name_a: str, name_b: str):
        self.cities_by_name[name_a].connect(self.cities_by_name[name_b])

    def get_city_by_name(self, name: str) -> CityGame:
        return self.cities_by_name[name]

    def get_city_by_id(self, id: int) -> CityGame:
        return self.cities_by_id[id]

    def get_start_city(self) -> CityGame:
        return self.cities_by_name[self.start_city]


def build_city_graph(game) -> CityGraph:
    """
    Собирает в ОЗУ граф городов для конкретной партии (game_code).

    1. Загружает статические города и связи (City, CityConnection).
    2. Накладывает динамическое состояние конкретной партии (CityState).
    """

    graph = CityGraph(game)

    # 1. Статическая карта
    for city in City.query.all():
        graph.add_city(city.id, city.name, city.color.value)

    for conn in CityConnection.query.all():
        graph.connect(conn.city.name, conn.connected_city.name)

    # 2. Динамика партии
    states = CityState.query.filter_by(game_id=game.code).all()
    for st in states:
        city = graph.get_city_by_name(st.base_city.name)
        city.load_from_db(st)

    return graph
