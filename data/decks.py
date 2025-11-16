import random
from typing import List, Optional, TYPE_CHECKING

from eng import db
from models import (
    Card, CardType,
    City,
    DeckOfCards, DeckOfDiseases
)


class CardGame:
    def __init__(self, card_id: int, name: str, type: str):
        self.card_id = card_id
        self.name = name
        self.type = type  # CITY / EVENT / EPIDEMIC


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
    
    def save_to_db(self, code: str):
        DeckOfCards.query.filter_by(game_id=code).delete()
    
        # сначала сохраняем draw_pile
        for order, cg in enumerate(self.draw_pile):
            entry = DeckOfCards(
                card_id=cg.card_id,
                game_id=code,
                order_index=order,
                in_game=True
            )
            db.session.add(entry)
    
        # затем сброс
        for order, cg in enumerate(self.discard_pile):
            entry = DeckOfCards(
                card_id=cg.card_id,
                game_id=code,
                order_index=order,
                in_game=False
            )
            db.session.add(entry)
    
        db.session.commit()
    
    def load_from_db(self, code: str):
        rows: list[DeckOfCards] = (
            DeckOfCards.query.filter_by(game_id=code)
            .order_by(DeckOfCards.in_game.desc(),
                      DeckOfCards.order_index.asc())
            .all()
        )
    
        self.draw_pile.clear()
        self.discard_pile.clear()
    
        for row in rows:
            card = row.card
            cg = CardGame(card.id, card.name, card.type.value)
            if row.in_game:
                self.draw_pile.append(cg)
            else:
                self.discard_pile.append(cg)


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

    def save_to_db(self, code: str):
        DeckOfDiseases.query.filter_by(game_id=code).delete()

        for order, city_id in enumerate(self.draw_pile):
            entry = DeckOfDiseases(
                city_id=city_id,
                game_id=code,
                order_index=order,
                in_game=True
            )
            db.session.add(entry)

        for order, city_id in enumerate(self.discard_pile):
            entry = DeckOfDiseases(
                city_id=city_id,
                game_id=code,
                order_index=order,
                in_game=False
            )
            db.session.add(entry)

        db.session.commit()

    def load_from_db(self, code: str):
        rows = (
            DeckOfDiseases.query.filter_by(game_id=code)
            .order_by(DeckOfDiseases.in_game.desc(),
                      DeckOfDiseases.order_index.asc())
            .all()
        )

        self.draw_pile.clear()
        self.discard_pile.clear()

        for row in rows:
            if row.in_game:
                self.draw_pile.append(row.city_id)
            else:
                self.discard_pile.append(row.city_id)


def build_decks(game):
    """
    Создает случайные колоды карт.
    Первые 10 карт не могут быть эпидемиями.
    
    Правила раздачи стартовых карт:
        2 игрока → 4 карты каждому → 8 верхних карт
        3 игрока → 3 карты каждому → 9 верхних карт
        4 игрока → 2 карты каждому → 8 верхних карт

    Возвращает player_deck и disease_deck.
    """
    player_deck = DeckCards(game)
    disease_deck = DeckDiseases(game)

    cards = Card.query.all()

    epidemic_cards = []
    normal_cards = []

    for c in cards:
        cg = CardGame(c.id, c.name, c.type.value)
        if c.type == CardType.EPIDEMIC:
            epidemic_cards.append(cg)
        else:
            normal_cards.append(cg)

    random.shuffle(normal_cards)

    safe_initial = normal_cards[:10]
    rest_normals = normal_cards[10:]

    random.shuffle(rest_normals)
    random.shuffle(epidemic_cards)

    player_deck.cards = safe_initial + rest_normals + epidemic_cards

    all_cities = City.query.all()
    disease_deck.cities = [c.id for c in all_cities]
    disease_deck.shuffle()
    
    player_deck.save_to_db(game.code)
    disease_deck.load_from_db(game.code)

    return player_deck, disease_deck
