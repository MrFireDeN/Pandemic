from __future__ import annotations

import json
from typing import TYPE_CHECKING

from data.enums import ColorType

if TYPE_CHECKING:
    from data.players import PlayerGame


class CityGame:
    def __init__(self, game, city_id: int, name: str, color: ColorType, graph: CityGraph = None):
        self.game = game
        self.id = city_id
        self.name = name
        self.color = color
        self.population: int = 0

        self.connections: list[CityGame] = []
        self.players: list[PlayerGame] = []

        self.has_station = False
        self.infection_cubes = {color: 0 for color in ColorType}

        self.graph = graph

    def connect(self, other: CityGame):
        if other not in self.connections:
            self.connections.append(other)
            other.connections.append(self)
            
    def is_connected(self, other: CityGame) -> bool:
        return other in self.connections

    def add_infection(self, color: ColorType, count: int = 1):
        """
        Добавляет инфекцию в город по заданному цвету.
        
        :param color: Цвет болезни (ColorEnum).
        :param count: Количество инфекции для добавления.
        """
        self.game.board.use_cube(color, count)
        if self.game.board.is_game_over:
            return 
        
        infection_count = self.infection_cubes[color] + count
        self.infection_cubes[color] = min(3, infection_count)

        if infection_count > 3:
            self.__trigger_outbreak(color)

    def remove_infection(self, color: ColorType, count: int = 1):
        """
        Убирает инфекцию из города по заданному цвету.
        
        :param color: Цвет болезни (ColorEnum).
        :param count: Количество инфекции для удаления.
        """
        current_infection = self.infection_cubes[color]
        new_infection_count = max(0, current_infection - count)
        self.infection_cubes[color] = new_infection_count
    
        self.game.board.return_cube(color, current_infection - new_infection_count)

    def __trigger_outbreak(self, color: ColorType):
        """Срабатывает при вспышке болезни в городе."""
        if self.graph is None:
            raise ValueError("Мама, где граф")

        self.graph.handle_outbreak(self, color)


class CityGraph:
    def __init__(self, game):
        self.game = game
        
        self.research_stations: list[CityGame] = []
        self.start_city: str = 'Atlanta'
        
        self.cities_by_name: dict[str, CityGame] = {}
        self.cities_by_id: dict[int, CityGame] = {}

        self.__visited_cities: set[CityGame] = set()

    def add_city(self, city_id: int, name: str, color: ColorType, population: int = 0):
        city = CityGame(self.game, city_id, name, color)
        city.population = population
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
        """Строит исследовательскую станцию в указанном городе."""
        city = self.get_city_by_name(city_name)
        if city is None or city.has_station:
            return

        city.has_station = True
        self.research_stations.append(city)

        if len(self.research_stations) > 6:
            self.research_stations.pop().has_station = False

        return

    def handle_outbreak(self, source_city: CityGame, color: ColorType):
        """Обрабатывает вспышку инфекции, распространяя болезнь в соседние города."""
        if source_city in self.__visited_cities:
            return

        self.__visited_cities.add(source_city)

        for city in source_city.connections:
            if city not in self.__visited_cities:
                city.add_infection(color)

    def clear_visited_cities(self):
        """Очищает список посещенных городов после обработки вспышки."""
        self.__visited_cities = set()
