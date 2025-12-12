import enum
from eng import db


# ------------------------------
# Enums
# ------------------------------
class ColorEnumDB(enum.Enum):
    red = "red"
    yellow = "yellow"
    blue = "blue"
    black = "black"


class CardTypeDB(enum.Enum):
    CITY = "CITY"
    EVENT = "EVENT"
    EPIDEMIC = "EPIDEMIC"


class GameStatusDB(enum.Enum):
    waiting = "waiting"
    active = "active"
    finished = "finished"
    aborted = "aborted"


# ------------------------------
# Справочники — static data
# ------------------------------
class CityModel(db.Model):
    __tablename__ = 'cities'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    color = db.Column(db.Enum(ColorEnumDB, name="color"), nullable=False)
    population = db.Column(db.Integer)

    connections_from = db.relationship(
        'CityConnectionModel',
        foreign_keys='CityConnectionModel.city_id',
        backref='city',
        cascade="all, delete-orphan",
        lazy='selectin'
    )
    connections_to = db.relationship(
        'CityConnectionModel',
        foreign_keys='CityConnectionModel.connected_city_id',
        backref='connected_city',
        cascade="all, delete-orphan",
        lazy='selectin'
    )


class CityConnectionModel(db.Model):
    __tablename__ = 'cities_connections'

    id = db.Column(db.Integer, primary_key=True)
    city_id = db.Column(db.Integer, db.ForeignKey("cities.id"), nullable=False)
    connected_city_id = db.Column(db.Integer, db.ForeignKey("cities.id"), nullable=False)


class RoleModel(db.Model):
    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.Text)


class EventModel(db.Model):
    __tablename__ = 'events'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    description = db.Column(db.Text)
    is_instant = db.Column(db.Boolean, default=False)
    is_single_use = db.Column(db.Boolean, default=True)


class CardModel(db.Model):
    __tablename__ = 'cards'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    description = db.Column(db.Text)
    type = db.Column(db.Enum(CardTypeDB), nullable=False)

    city_id = db.Column(db.Integer, db.ForeignKey("cities.id"), index=True)     # для городов
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"), index=True)    # для событий


# ------------------------------
# Игровая логика - dynamic data
# ------------------------------
class GameSessionModel(db.Model):
    __tablename__ = 'game_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(4), unique=True, index=True)
    status = db.Column(db.Enum(GameStatusDB), default=GameStatusDB.waiting, nullable=False)

    players             = db.relationship('PlayerModel', backref='game', lazy="selectin", cascade="all, delete-orphan")
    city_states         = db.relationship('CityStateModel', backref='game', lazy="selectin", cascade="all, delete")
    move_logs           = db.relationship('MoveLogModel', backref='game', lazy="selectin", cascade="all, delete")
    game_state          = db.relationship('GameStateModel', backref='game', uselist=False, cascade="all, delete-orphan")
    deck_of_cards       = db.relationship('DeckOfCardsModel', backref='game', lazy="selectin", cascade="all, delete")
    deck_of_diseases    = db.relationship('DeckOfDiseasesModel', backref='game', lazy="selectin", cascade="all, delete")


class GameStateModel(db.Model):
    __tablename__ = 'game_states'
    
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey("game_sessions.code"), nullable=False, index=True)

    # Очередность (Turn order): порядок ходов игроков (определяется по наибольшему населению в начале)
    turn_order = db.Column(db.Integer, default=0)

    # Статус хода игрока (PlayerModel turn status): каждый ход игрока включает в себя 4 шага
    player_turn_status = db.Column(db.Integer, default=0)

    # Индикатор вспышек (Outbreak indicator): количество вспышек в игре
    outbreak_indicator = db.Column(db.Integer, default=0)

    # Индикатор заражения (Infection indicator): количество эпидемий в игре
    infection_indicator = db.Column(db.Integer, default=0)

    # Кол-во станций (Number of stations): количество исследовательских станций
    research_stations = db.Column(db.Integer, default=0)

    # Кол-во кубиков каждого цвета (Cubes per color): остаток кубиков каждого цвета
    # Хранится как JSON строка (например, "[24, 24, 24, 24]")
    cubes_per_color = db.Column(db.Text, default="[24, 24, 24, 24]")

    # Состояние лекарств (Medicine state): статус лекарств (0 – не создано, 1 – создано, 2 – уничтожено)
    # Хранится как JSON строка (например, "[0, 0, 0, 0]")
    vaccines_state = db.Column(db.Text, default="[0, 0, 0, 0]")


class PlayerModel(db.Model):
    __tablename__ = 'players'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))

    game_id = db.Column(db.Integer, db.ForeignKey("game_sessions.code"), index=True, nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey("roles.id"))
    position_city_id = db.Column(db.Integer, db.ForeignKey("city_states.id"), index=True)

    actions_left = db.Column(db.Integer, default=4)
    
    role = db.relationship('RoleModel')


class MoveLogModel(db.Model):
    __tablename__ = 'move_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey("game_sessions.code"), index=True, nullable=False)
    payload = db.Column(db.Text)


class DeckOfCardsModel(db.Model):
    __tablename__ = 'deck_of_cards'
    
    id = db.Column(db.Integer, primary_key=True)

    card_id = db.Column(db.Integer, db.ForeignKey("cards.id"), nullable=False)
    game_id = db.Column(db.Integer, db.ForeignKey("game_sessions.code"), index=True, nullable=False)
    player_id = db.Column(db.Integer, db.ForeignKey("players.id"))

    order_index = db.Column(db.Integer)     # порядок в колоде
    in_game = db.Column(db.Boolean, default=True)

    card = db.relationship("CardModel", backref="card_instances")
    player = db.relationship("PlayerModel", backref="cards_owned")


class DeckOfDiseasesModel(db.Model):
    __tablename__ = 'deck_of_diseases'
    
    id = db.Column(db.Integer, primary_key=True)

    city_id = db.Column(db.Integer, db.ForeignKey("cities.id"), nullable=False)
    game_id = db.Column(db.Integer, db.ForeignKey("game_sessions.code"), index=True, nullable=False)

    order_index = db.Column(db.Integer)     # порядок в колоде
    in_game = db.Column(db.Boolean, default=True)

    city = db.relationship("CityModel")


class CityStateModel(db.Model):
    __tablename__ = 'city_states'

    id = db.Column(db.Integer, primary_key=True)

    city_id = db.Column(db.Integer, db.ForeignKey("cities.id"), nullable=False)
    game_id = db.Column(db.Integer, db.ForeignKey("game_sessions.code"), index=True, nullable=False)

    has_station = db.Column(db.Boolean, default=False)
    red = db.Column(db.Integer, default=0)
    yellow = db.Column(db.Integer, default=0)
    blue = db.Column(db.Integer, default=0)
    black = db.Column(db.Integer, default=0)

    base_city = db.relationship("CityModel")
    players_here = db.relationship("PlayerModel", backref="city_states")
