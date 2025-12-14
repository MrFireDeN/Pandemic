from __future__ import annotations

from typing import TYPE_CHECKING

import json

from data.enums import RoleType, ColorType

if TYPE_CHECKING:
    from data.cities import CityGame
    from data.decks import CardGame


class PlayerGame:
    def __init__(self, game, player_id: int, name: str, role_id: int, pos: CityGame):
        """
        Инициализирует игрока для игры.
        
        :param game: Игра, к которой относится игрок.
        :param player_id: Уникальный идентификатор игрока.
        :param name: Имя игрока.
        :param role_id: Роль игрока (связано с RoleType).
        :param pos: Начальная позиция игрока на игровом поле (город).
        """
        self.game = game
        self.id = player_id
        self.name = name
        self.role: RoleType = RoleType(role_id)
        self.pos: CityGame = pos
        self.actions_left = 4

    def move_to(self, city: CityGame, use_card: CardGame | None = None):
        """
        Перемещает игрока в указанный город, используя карты, если это необходимо.

        :param city: Город, в который нужно переместиться.
        :param use_card: Карта, которая может быть использована для перемещения (если применимо).
        """
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
        """
        Строит исследовательскую станцию в указанном городе.
        Если игрок — инженер, станция строится без карты, иначе используется карта.

        :param city: Город, в котором строится исследовательская станция.
        :param card: Карта, если используется для строительства станции.
        """
        if self.role == RoleType.ENGINEER:
            city.graph.build_research_station(city.name)
            self.__commit_action(f"Построена исследовательская станция в городе {city.name}")
            return

        if card is not None and card.is_city():
            city.graph.build_research_station(city.name)
            card.use()
            self.__commit_action(f"Использована карта для строительства исследовательской станции в городе {city.name}")
            return

    def cure_city(self, city: CityGame, color: ColorType):
        """
        Лечит город от инфекции указанного цвета.

        :param city: Город, который нужно вылечить.
        :param color: Цвет болезни (ColorEnum), который необходимо вылечить.
        """
        count = 3 if self.role == RoleType.DOCTOR else 1
        city.remove_infection(color, count)
        self.__commit_action(f"Лечение в городе {city.name} от болезни {color.name}")

    def discover_cure(self, color: ColorType, cards: list[CardGame]):
        """
        Игрок открывает лечение от болезни.

        :param color: Цвет болезни (ColorEnum), для которого открыто лечение.
        :param cards: Карты, использованные для открытия лечения.
        """
        count_color = len(cards)
        if self.role == RoleType.SCIENTIST:
            count_color += 1

        if count_color >= 5:
            self.game.board.cure_discovered(color)
            self.__commit_action(f"Открыто лечение от болезни {color.name}")

    def trade_card(self, card: CardGame, with_player: PlayerGame, give_or_apply: bool = True):
        """
        Обмен картами между игроками.

        :param card: Карта, которую передают.
        :param with_player: Игрок, с которым происходит обмен.
        :param give_or_apply: Если True — карта передается другому игроку, если False — карта возвращается.
        """
        if card is None or with_player is None:
            return

        card.player_owner = with_player if give_or_apply else self
        
        action = 'отдана' if give_or_apply else 'вернута'
        self.__commit_action(f"Карта {card.name} {action} игроку {with_player.name}")
        
    def use_card(self, card: CardGame):
        """
        Использует карту события (если это карта события).
        
        :param card: Карта, которую нужно использовать.
        """
        if card is None or not card.is_event():
            return
    
        card.use()
        self.__commit_action(f"Использована карта события {card.name}")

    def serialize(self):
        return json.dumps({
            'id': self.id,
            'name': self.name,
            'role': self.role.value,
            'position_city': self.pos.id if self.pos else None,
            'actions_left': self.actions_left,
        })

    @staticmethod
    def deserialize(data: dict, game):
        pos = game.cities.get_city_by_id(data['pos']) if data['pos'] else None
        player = PlayerGame(game, data['id'], data['name'], data['role'], pos)
        player.actions_left = data['actions_left']
        return player

    def __move_by_car(self, city: CityGame):
        self.pos = city
        self.__commit_action(f"Перемещен в город {city.name} по дороге")

    def __move_by_direct_flight(self, city: CityGame):
        self.pos = city
        self.__commit_action(f"Перелет в город {city.name} прямым рейсом")

    def __move_by_charter_flight(self, city: CityGame):
        self.pos = city
        self.__commit_action(f"Перелет в город {city.name} чартерным рейсом")

    def __move_by_research_flight(self, city: CityGame):
        self.pos = city
        self.__commit_action(f"Перелет в город {city.name} через исследовательскую станцию")

    def __move_by_cheat(self, city: CityGame):
        self.pos = city
        self.__commit_action(f"Перемещение в город {city.name} с нарушением правил", is_fair=False)

    def __commit_action(self, text: str | None = None, is_fair: bool = True):
        """
        Логирует действие игрока и проверяет завершение хода.

        :param text: Текстовое описание действия.
        :param is_fair: Флаг, указывающий, было ли действие честным.
        """
        self.actions_left -= 1

        if self.actions_left <= 0:
            self.game.notify_turn_ended()

        if is_fair:
            print(f'{self.name} {text}')
        else:
            print(f'cheating: {self.name} {text}')
