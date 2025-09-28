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