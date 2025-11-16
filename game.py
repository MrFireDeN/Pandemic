from models import Player
from eng import db

from data.cities import build_city_graph
from data.players import load_players, PlayerGame
from data.decks import build_decks
from data.boards import Board


class PandemicGame:
    def __init__(self, code=None):
        self.code = code
        self.phase = "waiting"
        
        self.board = Board(self)
        self.cities = build_city_graph(self)
        self.players = load_players(self)
        self.deck_cards, self.deck_diseases = build_decks(self)
        
    def add_player(self, player_db: Player):
        """
        Создаёт объект PlayerGame в памяти и добавляет его в сессию.
        player_db — это SQLAlchemy объект Player, который уже сохранён в БД.
        """
        pg = PlayerGame(
            game=self,
            id=player_db.id,
            name=player_db.name,
            role_id=player_db.role_id,
            pos=self.cities.get_start_city()
        )

        self.players.append(pg)

        return pg


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
