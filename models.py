from eng import db

class GameSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(16), unique=True, nullable=False, index=True)
    status = db.Column(db.String(32), default="waiting")  # waiting/active/finished

class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    session_code = db.Column(db.String(16), db.ForeignKey("game_session.code"), index=True)


class MoveLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_code = db.Column(db.String(16), index=True)
    payload = db.Column(db.Text)

class Cites(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    color = db.Column(db.String(64), nullable=False)
    population = db.Column(db.Integer, nullable=False)

class cities_connections(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    city_id = db.Column(db.Integer, db.ForeignKey("cities.id"), nullable=False)
    connected_city_id = db.Column(db.Integer, db.ForeignKey("cities.id"), nullable=False)

class events(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    description = db.Column(db.Text, nullable=False)
    is_instant = db.Column(db.Boolean, nullable=False)
    is_single_use = db.Column(db.Boolean, nullable=False)

class cards(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    description = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(64), nullable=False)

class roles(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    description = db.Column(db.Text, nullable=False)

class players(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey("roles.id"), nullable=False)
    position_city_id = db.Column(db.Integer, db.ForeignKey("cities.id"), nullable=False)
    player_cards = db.Column(db.Integer, nullable=False)
    actions_left = db.Column(db.Integer, nullable=False)

class vaccines(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    color = db.Column(db.String(64), nullable=False)
    status = db.Column(db.String(64), nullable=False)

class cards_in_desk(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    card_id = db.Column(db.Integer, db.ForeignKey("cards.id"), nullable=False)
    player_id = db.Column(db.Integer, db.ForeignKey("players.id"), nullable=False)
    serial_number = db.Column(db.Integer, nullable=False)

class viruses_desk(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    city_id = db.Column(db.Integer, db.ForeignKey("cities.id"), nullable=False)
    serial_number = db.Column(db.Integer, nullable=False)
    in_game = db.Column(db.Boolean, nullable=False)