from models import Player
from eng import db

from data.cities import build_city_graph, CityGame
from data.players import load_players, PlayerGame
from data.decks import build_decks, CardGame
from data.boards import Board


class PandemicGame:
    def __init__(self, code=None):
        self.code = code
        self.phase = "waiting"
        
        self.board = Board(self)
        self.cities = build_city_graph(self)
        self.players = load_players(self)
        self.deck_cards, self.deck_diseases = build_decks(self)
        
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

    def move_player(self, player_id: int, to_city: str, use_card: CardGame | None = None):
        player = self.__search_player(player_id)
        if player is None:
            return 401

        city = self.cities.get_city_by_name(to_city)
        if city is None:
            return 402

        player.move_to(city, use_card)
        return 200

    def cure_city_player(self, player_id: int, city_name: str, color: str):
        player = self.__search_player(player_id)
        if player is None:
            return 401

        city = self.cities.get_city_by_name(city_name)
        if city is None:
            return 402

        player.cure_disease(city, color)
        return 200

    def use_event_player(self, player_id: int, card: CardGame):
        pass

    def build_research_station_player(self, player_id: int, city_name: str, card: CardGame):
        player = self.__search_player(player_id)
        if player is None:
            return 401

        city = self.cities.get_city_by_name(city_name)
        if city is None:
            return 402

        player.build_research_station(city, card)
        return 200

    def trade_card_player(self, from_player_id: int, to_player_id, card: CardGame):
        from_player = self.__search_player(from_player_id)
        to_player = self.__search_player(to_player_id)

        if from_player is None or to_player is None:
            return 401

        from_player.trade_card(card, to_player)
        return 200

    def discover_cure_player(self, player_id: int, color: str, cards: list[CardGame]):
        player = self.__search_player(player_id)
        if player is None:
            return 401

        player.discover_cure(color, cards)
        return 200

    def notify_player_moved(self):
        pass

    def notify_turn_ended(self):
        pass

    def notify_player_drew_cards(self):
        pass

    def notify_disease_spread(self):
        pass

    def notify_epidemic(self):
        pass

    def notify_outbreak(self):
        pass

    def notify_disease_cured(self):
        pass

    def notify_game_over(self):
        pass

    def __search_player(self, player_id: int) -> PlayerGame | None:
        for player in self.players:
            if player.id == player_id:
                return player
        return None



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
