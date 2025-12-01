from __future__ import annotations

import random
from typing import List, Optional, TYPE_CHECKING


if TYPE_CHECKING:
    from data.enums import CardType
    from data.players import PlayerGame


class CardGame:
    def __init__(self, card_id: int, name: str, card_type: CardType):
        self.id = card_id
        self.name = name
        self.type = card_type

        self.player_owner: PlayerGame | None = None

    def is_type(self, card_type: CardType) -> bool:
        return self.type == card_type

    def is_city(self) -> bool:
        return self.is_type(CardType.CITY)

    def is_event(self) -> bool:
        return self.is_type(CardType.EVENT)

    def is_epidemic(self) -> bool:
        return self.is_type(CardType.EPIDEMIC)

    def serialize(self):
        # TODO
        pass

    def deserialize(self):
        # TODO
        pass


class DeckCards:
    def __init__(self, game):
        self.game = game
        self.draw_pile: List[CardGame] = []
        self.discard_pile: List[CardGame] = []
    
    def shuffle(self):
        random.shuffle(self.draw_pile)

    def draw(self) -> Optional[CardGame]:
        if not self.draw_pile:
            return None
        return self.draw_pile.pop(0)
    
    def discard(self, card: CardGame):
        """Кладёт карту в сброс."""
        self.discard_pile.append(card)
        
    def serialize(self):
        pass
    
    def deserialize(self):
        pass


class DeckDiseases:
    def __init__(self, game):
        self.game = game
        self.draw_pile: List[int] = []
        self.discard_pile: List[int] = []

    def shuffle(self):
        random.shuffle(self.draw_pile)

    def draw(self) -> Optional[int]:
        if not self.draw_pile:
            return None
        return self.draw_pile.pop(0)

    def discard(self, city_id: int):
        self.discard_pile.append(city_id)

    def return_discard_on_top(self):
        """Эпидемия — перемешиваем discard и кладём сверху draw."""
        random.shuffle(self.discard_pile)
        self.draw_pile = self.discard_pile + self.draw_pile
        self.discard_pile = []

    def serialize(self):
        pass
    
    def deserialize(self):
        pass
