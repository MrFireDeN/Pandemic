from flask import Blueprint, jsonify, request
from eng import db, socketio
from models import GameSession, Player
from flask_socketio import emit, join_room
import secrets

api_bp = Blueprint("api", __name__)

@api_bp.route("/health")
def health():
    return jsonify({"status": "ok"})

@api_bp.post("/host/create")
def host_create():
    code = secrets.token_hex(2).upper()
    print(code)
    session = GameSession(code=code, status="waiting")
    db.session.add(session)
    # db.session.commit()

    return jsonify({"code": code})

@socketio.on("host_join")
def on_host_join(data):
    code = data.get("code")
    join_room(code)
    emit("host_ready", {"code": code}, to=code)

@socketio.on("player_join")
def on_player_join(data):
    code = data.get("code")
    name = data.get("name")
    player = Player(name=name, session_code=code)
    db.session.add(player)
    db.session.commit()
    join_room(code)
    emit("player_joined", {"name": name}, to=code)

@socketio.on("start_game")
def on_start_game(data):
    code = data.get("code")
    emit("game_started", {}, to=code)

@socketio.on("player_action")
def on_player_action(data):
    code = data.get("code")
    action = data.get("action")
    emit("action_broadcast", {"action": action}, to=code)
