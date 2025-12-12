from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from data.enums import ColorType
    from data.players import PlayerGame


class CityGame:
    def __init__(self, game, city_id: int, name: str, color: str | ColorType, graph: CityGraph = None):
        self.game = game
        self.id = city_id
        self.name = name

        if isinstance(color, str):
            color = ColorType[color]
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

        self.graph = graph

    def connect(self, other: CityGame):
        if other not in self.connections:
            self.connections.append(other)
            other.connections.append(self)
            
    def is_connected(self, other: CityGame) -> bool:
        return other in self.connections

    def add_infection(self, color: str | ColorType, count: int = 1):
        if isinstance(color, ColorType):
            color = color.name

        infection_count = self.infection_cubes[color] + count
        self.infection_cubes[color] = min(3, infection_count)

        if infection_count > 3:
            self.__trigger_outbreak(color)

    def remove_infection(self, color: str | ColorType, count: int = 1):
        if isinstance(color, ColorType):
            color = color.name

        self.infection_cubes[color] = max(0, self.infection_cubes[color] - count)

    def __trigger_outbreak(self, color: str | ColorType):
        if self.graph is None:
            raise ValueError("Мама, где граф")

        self.graph.handle_outbreak(self, color)
        
    def serialize(self):
        pass
    
    def deserialize(self):
        pass


class CityGraph:
    def __init__(self, game):
        self.game = game
        
        self.research_stations: list[CityGame] = []
        self.start_city: str = 'Atlanta'
        
        self.cities_by_name: dict[str, CityGame] = {}
        self.cities_by_id: dict[int, CityGame] = {}

        self.__visited_cities: set[CityGame] = set()

    def add_city(self, city_id: int, name: str, color: str | ColorType):
        if isinstance(color, str):
            color = ColorType[color]

        city = CityGame(self.game, city_id, name, color)
        city.graph = self
        self.cities_by_name[name] = city
        self.cities_by_id[city_id] = city

    def connect(self, name_a: str, name_b: str):
        self.cities_by_name[name_a].connect(self.cities_by_name[name_b])

    def get_city_by_name(self, name: str) -> CityGame:
        return self.cities_by_name[name]

    def get_city_by_id(self, city_id: int) -> CityGame:
        return self.cities_by_id[city_id]

    def get_start_city(self) -> CityGame:
        return self.cities_by_name[self.start_city]

    def build_research_station(self, city_name: str):
        city = self.get_city_by_name(city_name)
        if city is None or city.has_station:
            return

        city.has_station = True
        self.research_stations.append(city)

        if len(self.research_stations) > 6:
            self.research_stations.pop().has_station = False

        return

    def handle_outbreak(self, source_city: CityGame, color: str | ColorType):
        if source_city in self.__visited_cities:
            return

        self.__visited_cities.add(source_city)

        for city in source_city.connections:
            if city not in self.__visited_cities:
                city.add_infection(color)

    def clear_visited_cities(self):
        self.__visited_cities = set()


'''
def build_city_graph(game) -> CityGraph:
    """
    Собирает в ОЗУ граф городов для конкретной партии (game_code).

    1. Загружает статические города и связи (CityModel, CityConnectionModel).
    2. Накладывает динамическое состояние конкретной партии (CityStateModel).
    """

    graph = CityGraph(game)

    # 1. Статическая карта
    for city in CityModel.query.all():
        graph.add_city(city.id, city.name, city.color.value)

    for conn in CityConnectionModel.query.all():
        graph.connect(conn.city.name, conn.connected_city.name)

    # 2. Динамика партии
    states = CityStateModel.query.filter_by(game_id=game.code).all()
    for st in states:
        city = graph.get_city_by_name(st.base_city.name)
        city.load_from_db(st)

    graph.add_research_station(graph.get_start_city().name)

    return graph
'''