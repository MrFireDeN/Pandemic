from models import Player, GameSession
from data import cities
from eng import db

class PandemicGame:
    def __init__(self, code=None, db_ref: GameSession = None):
        self.code = code
        self.db_ref = db_ref
        self.cities = cities.build_city_graph()
        self.state = {"phase": "lobby"}
        self.players: list[Player] = []

    def refresh_data(self):
        """Reload shadow data from DB into memory (in case of server restart)."""
        if not self.db_ref:
            self.db_ref = GameSession.query.filter_by(code=self.code).first()
        if not self.db_ref:
            raise ValueError(f"No DB session found for {self.code}")

        self.state["phase"] = self.db_ref.status
        # можно подгрузить игроков, карты и т.д.

    def commit_to_db(self):
        """Commit current in-memory state into DB."""
        if not self.db_ref:
            # создать, если не было
            self.db_ref = GameSession(code=self.code)
            db.session.add(self.db_ref)

        self.db_ref.status = self.state["phase"]
        self.db_ref.turn = self.state.get("turn", 0)
        db.session.commit()

    def get_start_city(self):
        return self.cities.get_start_city().name


class Sessions:
    def __init__(self):
        self.sessions: list[PandemicGame] = []

    def add_session(self, session: PandemicGame):
        self.sessions.append(session)

    def create_session(self, code: str, db_ref: GameSession = None) -> PandemicGame:
        session = PandemicGame(code=code, db_ref=db_ref)
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
        return Sessions()

SESSIONS = Sessions()