from eng import db

class GameSession(db.Model):
    __tablename__ = 'game_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(16), unique=True, index=True)
    status = db.Column(db.String(32), default="waiting")
    
    players = db.relationship('Player', backref='game_session', lazy=True)
    move_logs = db.relationship('MoveLog', backref='game_session', lazy=True)

class GameState(db.Model):
    __tablename__ = 'game_states'
    
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey("game_sessions.id"), index=True)
    
    # Очередность (Turn order): порядок ходов игроков (определяется по наибольшему населению в начале)
    turn_order = db.Column(db.Integer, default=0)
    
    # Статус хода игрока (Player turn status): каждый ход игрока включает в себя 4 шага
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
    
    game_session = db.relationship('GameSession', backref='game_state')
    
class Player(db.Model):
    __tablename__ = 'players'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    session_code = db.Column(db.String(16), db.ForeignKey("game_sessions.code"), index=True)
    role_id = db.Column(db.Integer, db.ForeignKey("roles.id"))
    position_city_id = db.Column(db.Integer, db.ForeignKey("cities.id"))
    player_cards = db.Column(db.Integer)
    actions_left = db.Column(db.Integer)
    
    role = db.relationship('Role', backref='players')
    position_city = db.relationship('City', foreign_keys=[position_city_id], backref='players_at_position')
    cards_in_hand = db.relationship('CardInHand', backref='player')

class MoveLog(db.Model):
    __tablename__ = 'move_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    session_code = db.Column(db.String(16), db.ForeignKey("game_sessions.code"), index=True)
    payload = db.Column(db.Text)

class City(db.Model):
    __tablename__ = 'cities'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    color = db.Column(db.String(64))
    population = db.Column(db.Integer)
    
    connections = db.relationship('CityConnection', foreign_keys='CityConnection.city_id', backref='city')
    connected_cities = db.relationship('CityConnection', foreign_keys='CityConnection.connected_city_id', backref='connected_city')
    virus_cards = db.relationship('DeckOfDiseases', backref='city')

class CityConnection(db.Model):
    __tablename__ = 'cities_connections'
    
    id = db.Column(db.Integer, primary_key=True)
    city_id = db.Column(db.Integer, db.ForeignKey("cities.id"))
    connected_city_id = db.Column(db.Integer, db.ForeignKey("cities.id"))

class Event(db.Model):
    __tablename__ = 'events'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    description = db.Column(db.Text)
    is_instant = db.Column(db.Boolean)
    is_single_use = db.Column(db.Boolean)

class Card(db.Model):
    __tablename__ = 'cards'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    description = db.Column(db.Text)
    type = db.Column(db.String(64))
    cards_in_hand = db.relationship('CardInHand', backref='card')

class Role(db.Model):
    __tablename__ = 'roles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    description = db.Column(db.Text)

class Vaccine(db.Model):
    __tablename__ = 'vaccines'
    
    id = db.Column(db.Integer, primary_key=True)
    color = db.Column(db.String(64))
    status = db.Column(db.String(64))

class CardInHand(db.Model):
    __tablename__ = 'cards_in_desk'
    
    id = db.Column(db.Integer, primary_key=True)
    card_id = db.Column(db.Integer, db.ForeignKey("cards.id"))
    player_id = db.Column(db.Integer, db.ForeignKey("players.id"))
    serial_number = db.Column(db.Integer)

class DeckOfDiseases(db.Model):
    __tablename__ = 'viruses_desk'
    
    id = db.Column(db.Integer, primary_key=True)
    city_id = db.Column(db.Integer, db.ForeignKey("cities.id"))
    serial_number = db.Column(db.Integer)
    in_game = db.Column(db.Boolean)