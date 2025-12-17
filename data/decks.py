from __future__ import annotations

import json
import random
from typing import List, Optional, TYPE_CHECKING

from data.enums import CardType

if TYPE_CHECKING:
    from data.players import PlayerGame


class CardGame:
    def __init__(self, card_id: int, name: str, card_type: CardType, deck):
        """
        Инициализирует карту для игры.
        
        :param card_id: Уникальный идентификатор карты.
        :param name: Название карты.
        :param card_type: Тип карты (CardType).
        :param deck: Колода, к которой относится эта карта.
        """
        self.id = card_id
        self.name = name
        self.type = card_type

        self.player_owner: PlayerGame | None = None
        
        self.deck = deck
        
    def use(self):
        """
        Использует карту, если это карта события.
        Если карта события, выполняется её эффект, а затем она сбрасывается.
        """
        if self.is_event():
            print("ну типа произошел ивет")
        
        if self.deck is not None:
            self.deck.discard(self)

    def is_type(self, card_type: CardType) -> bool:
        """
        Проверяет, является ли карта заданного типа.
        
        :param card_type: Тип карты для проверки.
        :return: True, если карта указанного типа, иначе False.
        """
        return self.type == card_type

    def is_city(self) -> bool:
        """
        Проверяет, является ли карта картой города.
        
        :return: True, если карта типа CITY, иначе False.
        """
        return self.is_type(CardType.CITY)

    def is_event(self) -> bool:
        """
        Проверяет, является ли карта картой события.
        
        :return: True, если карта типа EVENT, иначе False.
        """
        return self.is_type(CardType.EVENT)

    def is_epidemic(self) -> bool:
        """
        Проверяет, является ли карта картой эпидемии.
        
        :return: True, если карта типа EPIDEMIC, иначе False.
        """
        return self.is_type(CardType.EPIDEMIC)


class DeckCards:
    def __init__(self, game):
        """
        Инициализирует колоду карт для игры.

        :param game: Игра, к которой относится эта колода.
        """
        self.game = game
        self.draw_pile: List[CardGame] = []
        self.discard_pile: List[CardGame] = []

    def shuffle(self):
        """
        Перемешивает колоду. Первые 10 карт не могут быть эпидемиями.
        Если в первых 10 картах есть эпидемия, колода перемешивается заново.
        """
        while True:
            random.shuffle(self.draw_pile)
            if all(not card.is_epidemic() for card in self.draw_pile[:10]):
                break

    def draw(self) -> Optional[CardGame]:
        """
        Вытягивает карту из колоды. Если колода пуста, завершает игру.

        :return: Вытянутая карта или None, если колода пуста.
        """
        if not self.draw_pile:
            self.game.board.trigger_game_over()
            return None
        
        # TODO: изменить логику карт в руке
        card = self.draw_pile.pop(0)
        self.draw_pile.append(card)
        
        if card.player_owner is not None:
            self.game.board.trigger_game_over()
            return None
        
        return card
    
    def discard(self, card: CardGame):
        """
        Добавляет карту в сброс.

        :param card: Карта, которую нужно сбросить.
        """
        self.discard_pile.append(card)


class DeckDiseases:
    def __init__(self, game):
        self.game = game
        self.draw_pile: List[CardGame] = []
        self.discard_pile: List[CardGame] = []

    def shuffle(self):
        random.shuffle(self.draw_pile)

    def draw(self) -> Optional[CardGame]:
        """
        Вытягивает карту из колоды. Если колода пуста, завершает игру.

        :return: Вытянутая карта или None, если колода пуста.
        """
        if not self.draw_pile:
            self.game.board.trigger_game_over()
            return None
        return self.draw_pile.pop(0)

    def discard(self, card: CardGame):
        """
        Добавляет карту в сброс.

        :param card: Карта, которую нужно сбросить.
        """
        self.discard_pile.append(card)

    def return_discard_on_top(self):
        """Эпидемия — перемешиваем discard и кладём сверху draw."""
        random.shuffle(self.discard_pile)
        self.draw_pile = self.discard_pile + self.draw_pile
        self.discard_pile = []

    def draw_last(self):
        """
        Вытягивает карту из-под низа колоды. Если колода пуста, завершает игру.

        :return: Вытянутая карта или None, если колода пуста.
        """
        if not self.draw_pile:
            self.game.board.trigger_game_over()
            return None
        return self.draw_pile.pop()
