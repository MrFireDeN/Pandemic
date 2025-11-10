from models import Player, GameSession, MoveLog, City, DeckOfCards
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

    def move(self, player: Player, to_city: str, transport, card):
        if self.state["phase"] != "active":
            return 403
        
        new_city = db.session.query(City).filter_by(name=to_city).first()

        if not new_city:
            return 403

        if player.actions_left <= 0:
            return 403

        log = MoveLog(session_code=self.code, 
                      payload=f'{player.name} moved from {player.position_city.name} to {new_city.name}')
        
        player.position_city_id = new_city.id
        player.actions_left -= 1

        db.session.add(log)
        db.session.commit()

        return 200

    def add_player(self, player: Player):
        self.players.append(player)

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