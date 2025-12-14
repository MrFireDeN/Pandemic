from abc import ABC, abstractmethod


class Observer(ABC):
    @abstractmethod
    def update(self, message):
        pass

class Subject(ABC):
    @abstractmethod
    def add_observer(self, observer: Observer):
        pass

    @abstractmethod
    def remove_observer(self, observer: Observer):
        pass

    @abstractmethod
    def notify_observers(self, message):
        pass


from data.cities import CityGame, CityGraph
from data.players import PlayerGame
from data.decks import CardGame, DeckCards, DeckDiseases
from data.boards import Board
from data.enums import *


class PandemicGame(Subject):
    def __init__(self, code=None):
        from data.repo import GameRepository
        
        self.code = code
        self.phase = "waiting"
        self.difficult = Difficult.easy
        
        self.board = Board(self)
        self.players = []
        self.cities = GameRepository.initialize_cities(self)
        self.deck_cards, self.deck_diseases = GameRepository.initialize_decks(self)

        self._observers = []
        
        GameRepository.save_game(self)
        
    def add_player(self, player_id, name, role_id):
        pg = PlayerGame(
            game=self,
            player_id=player_id,
            name=name,
            role_id=role_id,
            pos=self.cities.get_start_city()
        )

        self.players.append(pg)

        return pg

    def start_game(self):
        self.phase = "playing"

        self.notify_observers({"event": "game_started", "phase": self.phase})
        self.__save()
        return 200

    def move_player(self, player_id: int, to_city: str, use_card: CardGame | None = None):
        player = self.__search_player(player_id)
        if player is None:
            return {"status": 401, "message": "Player not found"}

        city = self.cities.get_city_by_name(to_city)
        if city is None:
            return {"status": 402, "message": "City not found"}

        player.move_to(city, use_card)
        self.notify_observers({"event": "player_moved", "player_id": player_id, "new_city": to_city})
        self.__save()
        return {"status": 200, "message": "Player moved successfully"}

    def cure_city_player(self, player_id: int, city_name: str, color: ColorType):
        player = self.__search_player(player_id)
        if player is None:
            return {"status": 401, "message": "Player not found"}

        city = self.cities.get_city_by_name(city_name)
        if city is None:
            return {"status": 402, "message": "City not found"}

        player.cure_city(city, color)
        self.notify_observers({"event": "city_cured", "player_id": player_id, "city": city_name, "color": color})
        self.__save()
        return {"status": 200, "message": "City cured successfully"}

    def use_event_player(self, player_id: int, card: CardGame):
        player = self.__search_player(player_id)
        if player is None:
            return {"status": 401, "message": "Player not found"}

        player.use_card(card)
        self.notify_observers({"event": "event_used", "player_id": player_id, "card": card})
        self.__save()
        return {"status": 200, "message": "Event used successfully"}

    def build_research_station_player(self, player_id: int, city_name: str, card: CardGame):
        player = self.__search_player(player_id)
        if player is None:
            return {"status": 401, "message": "Player not found"}

        city = self.cities.get_city_by_name(city_name)
        if city is None:
            return {"status": 402, "message": "City not found"}

        player.build_research_station(city, card)
        self.notify_observers({"event": "research_station_built", "player_id": player_id, "city": city_name})
        self.__save()
        return {"status": 200, "message": "Research station built successfully"}

    def trade_card_player(self, from_player_id: int, to_player_id: int, card: CardGame):
        from_player = self.__search_player(from_player_id)
        to_player = self.__search_player(to_player_id)

        if from_player is None or to_player is None:
            return {"status": 401, "message": "Player not found"}

        from_player.trade_card(card, to_player)
        self.notify_observers({"event": "card_traded", "from_player_id": from_player_id, "to_player_id": to_player_id, "card": card})
        self.__save()
        return {"status": 200, "message": "Card traded successfully"}

    def discover_cure_player(self, player_id: int, color: ColorType, cards: list[CardGame]):
        player = self.__search_player(player_id)
        if player is None:
            return {"status": 401, "message": "Player not found"}

        player.discover_cure(color, cards)
        self.notify_observers({"event": "cure_discovered", "player_id": player_id, "color": color, "cards_used": cards})
        self.__save()
        return {"status": 200, "message": "Cure discovered successfully"}

    def notify_player_moved(self):
        self.notify_observers({"event": "player_moved"})

    def notify_turn_ended(self):
        self.board.turn_order = (self.board.turn_order + 1) % len(self.players)
        self.notify_observers({"event": "turn_ended", "turn_order": self.board.turn_order})
        
    def notify_player_drew_cards(self):
        self.notify_observers({"event": "player_drew_cards"})

    def notify_disease_spread(self):
        self.notify_observers({"event": "disease_spread"})

    def notify_epidemic(self):
        self.notify_observers({"event": "epidemic"})

    def notify_outbreak(self):
        self.notify_observers({"event": "outbreak"})

    def notify_disease_cured(self):
        self.notify_observers({"event": "disease_cured"})

    def notify_game_over(self, is_victory=False):
        self.notify_observers({"event": "game_over", "victory": is_victory})

    def serialize(self):
        """
        Сериализует текущую игру в формат, который можно сохранить в базе данных.
        """
        return {
            "code": self.code,
            "phase": self.phase,
        }

    def deserialize(self, data):
        """
        Восстанавливает игру из сериализованных данных.
        """
        self.code = data["code"]
        self.phase = data["phase"]

    def add_observer(self, observer: Observer):
        if observer not in self._observers:
            self._observers.append(observer)

    def remove_observer(self, observer: Observer):
        if observer in self._observers:
            self._observers.remove(observer)

    def notify_observers(self, message):
        for observer in self._observers:
            observer.update(message)

    def __search_player(self, player_id: int) -> PlayerGame | None:
        for player in self.players:
            if player.id == player_id:
                return player
        return None

    def __save(self):
        from data.repo import GameRepository
        
        GameRepository.save_game(self)


class Sessions:
    _instance = None
    
    def __init__(self):
        self.sessions: list[PandemicGame] = []

    def add_session(self, session: PandemicGame):
        self.sessions.append(session)

    def create_session(self, code: str) -> PandemicGame:
        session = PandemicGame(code=code)
        self.add_session(session)
        return session

    def remove_session(self, session: PandemicGame):
        self.sessions.remove(session)

    def get_session(self, code) -> PandemicGame | None:
        for session in self.sessions:
            if session.code == code:
                return session
        return None

    @staticmethod
    def get_instance():
        if Sessions._instance is None:
            Sessions._instance = Sessions()
        return Sessions._instance


SESSIONS = Sessions()
