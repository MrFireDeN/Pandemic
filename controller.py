from flask import Blueprint, jsonify, request
from flask_socketio import emit, join_room

from eng import db, socketio
from models import GameSessionModel, PlayerModel, CityModel, RoleModel, GameStatusDB

import secrets

from game import SESSIONS, PandemicGame, Observer
from data.repo import GameRepository

from typing import Any, Dict, Optional

api = Blueprint("api", __name__)


def load_game_sessions(app):
    """Загружаем все игровые сессии из базы данных."""
    with app.app_context():  # Контекст приложения создается с использованием переданного объекта app
        game_sessions = GameSessionModel.query.all()

        for gs in game_sessions:
            game = GameRepository.load_game(gs.code)
            GameRepository.save_game(game)
            SESSIONS.add_session(game)
            attach_controller(game)


class Controller(Observer):
    def __init__(self, game_code: str | None = None):
        self.game_code = game_code

    def update(self, message: Any):
        payload: Dict[str, Any] = {"game_id": self.game_code}

        if isinstance(message, dict):
            payload.update(message)
            text = message.get("message") or message.get("event") or str(message)
        else:
            text = str(message)
            payload["message"] = text

        payload["text"] = text

        socketio.emit("game:log", payload, room=self.game_code)


controllers: Dict[str, Controller] = {}


def attach_controller(game: PandemicGame) -> Controller:
    """
    Подписывает контроллер на события игры и сохраняет ссылку.
    """
    controller = controllers.get(game.code)
    if controller is None:
        controller = Controller(game_code=game.code)
        controllers[game.code] = controller
        game.add_observer(controller)
    return controller


def _get_game_or_load(code: str) -> PandemicGame | None:
    """
    Возвращает игру из оперативной памяти или загружает её из БД.
    """
    game = SESSIONS.get_session(code)
    if game:
        return game

    game = GameRepository.load_game(code)
    if game:
        SESSIONS.add_session(game)
        attach_controller(game)
    return game


def _get_player_from_game(game: PandemicGame, player_id: int):
    for player in game.players:
        if player.id == player_id:
            return player
    return None


def _get_card_from_game(game: PandemicGame, card_id: Optional[int]):
    if card_id is None or not hasattr(game, "deck_cards"):
        return None

    try:
        searched_id = int(card_id)
    except Exception:
        return None

    for card in list(game.deck_cards.draw_pile) + list(game.deck_cards.discard_pile):
        if card.id == searched_id:
            return card
    return None


def _emit_log(game_code: str, text: str, payload: Optional[Dict[str, Any]] = None):
    data = payload.copy() if payload else {}
    data.update({"game_id": game_code, "text": text})
    socketio.emit("game:log", data, room=game_code)

@api.route("/health")
def health():
    return jsonify({"status": "ok"})

@api.post("/host/create")
def host_create():
    code = secrets.token_hex(2).upper()

    session = GameSessionModel(code=code, status=GameStatusDB.waiting)
    db.session.add(session)
    db.session.commit()

    game = SESSIONS.create_session(code)
    attach_controller(game)

    return jsonify({
        "status": "ok",
        "code": code,
        "phase": game.phase,
    })

@socketio.on("host_join")
def on_host_join(data):
    code = data.get("code")
    join_room(code)

    game = _get_game_or_load(code)
    if not game:
        emit("error", {"message": f"Session {code} not found"})
        return

    emit(
        "host_ready",
        {
            "code": code,
            "players": [p.name for p in game.players]
        }
    )

@socketio.on("player_join")
def on_player_join(data):
    code = data.get("code")
    player_name = data.get("name")
    role_id = data.get("role")

    game = _get_game_or_load(code)
    if not game:
        emit("error", {"message": f"Session {code} not found"})
        return

    # Проверка дубликатов
    if any(p.name == player_name for p in game.players):
        emit("error", {"message": f"PlayerModel '{player_name}' already exists"})
        return

    role = db.session.query(RoleModel).filter_by(id=role_id).first()
    if not role:
        emit("error", {"message": f"Role '{role_id}' not found"})
        return
    role_name = role.name

    start_city_name = game.cities.start_city
    start_city = CityModel.query.filter_by(name=start_city_name).first()
    if not start_city:
        emit("error", {"message": f"Start city '{game.START_CITY}' not found"})
        return

    db_player = PlayerModel(
        name=player_name,
        game_id=code,
        role_id=role.id,
        position_city_id=start_city.id
    )
    db.session.add(db_player)
    db.session.commit()
    game.add_player(db_player.id, player_name, role_id)

    join_room(code)

    emit("player_joined", {
        "name": player_name,
        "role": role_name
    }, to=code)

@socketio.on("start_game")
def on_start_game(data):
    code = data.get("code")

    game = _get_game_or_load(code)
    if not game:
        emit("error", {"message": f"Session {code} not found"})
        return

    result = game.start_game()
    if result.get("status") == 200:
        emit("game_started", result, to=code)
    else:
        emit("error", {"message": result.get("message", "Не удалось начать игру")}, room=request.sid)

# ------------------------------
# REST endpoints — PlayerModel actions
# ------------------------------

@api.post("/player/move")
def post_player_move() -> Any:
    data = request.get_json() or {}

    player_id = data.get("player_id")
    to_city_name = data.get("to_city")
    card_id = data.get("card_id")

    if not all([player_id, to_city_name]):
        return jsonify({"status": "error", "message": "Missing required fields"}), 400
    
    # Проверяем игрока и целевой город
    player_model = PlayerModel.query.get(player_id)
    if not player_model:
        return jsonify({"status": "error", "message": "PlayerModel not found"}), 404

    game = _get_game_or_load(player_model.game_id)
    if not game:
        return jsonify({"status": "error", "message": f"Session {player_model.game_id} not found"}), 404

    player = _get_player_from_game(game, player_id)
    if not player:
        return jsonify({"status": "error", "message": "Player not in game"}), 404

    card = _get_card_from_game(game, card_id)

    try:
        result = game.move_player(player_id, to_city_name, card)
        status = result.get("status", 500)

        if status == 200:
            notify_player_moved(player_model.game_id, player, to_city_name)
            _emit_log(player_model.game_id, f"{player.name} переместился в {to_city_name}", {"player_id": player_id})
        return jsonify(result), status
    except Exception as e:
        db.session.rollback()
        print(f"[MoveError] {e}")
        return jsonify({"status": "error", "message": "Internal error"}), 500

@api.post("/player/use-event")
def post_player_use_event() -> Any:
    """Use an event card.

    Expected JSON:
    {
    "game_id": str,
    "player_id": str,
    "event_card_id": str,
    "payload": dict | null # event-specific arguments (city, target, etc.)
    }
    """
    data = request.get_json() or {}

    game_id = data.get("game_id")
    player_id = data.get("player_id")
    card_id = data.get("event_card_id")

    if not all([game_id, player_id, card_id]):
        return jsonify({"status": "error", "message": "Missing required fields"}), 400

    game = _get_game_or_load(game_id)
    if not game:
        return jsonify({"status": "error", "message": "Game not found"}), 404

    card = _get_card_from_game(game, int(card_id))
    player = _get_player_from_game(game, int(player_id))

    if not player:
        return jsonify({"status": "error", "message": "Player not in game"}), 404
    if not card:
        return jsonify({"status": "error", "message": "Card not found"}), 404

    result = game.use_event_player(int(player_id), card)
    status = result.get("status", 500)

    if status == 200:
        socketio.emit("player:used_event", {"player_id": player_id, "card_id": card_id}, room=game_id)
        _emit_log(game_id, f"{player.name} использовал карту события {card.name}")

    return jsonify(result), status

@api.post("/player/build-research-station")
def post_player_build_research_station() -> Any:
    """Build a research station in a city.
    
    
    Expected JSON:
    {
    "game_id": str,
    "player_id": str,
    "city": str,
    "card_id": str | null # optional per "soft rules"
    }
    """
    data = request.get_json() or {}
    game_id = data.get("game_id")
    player_id = data.get("player_id")
    city_name = data.get("city")
    card_id = data.get("card_id")

    if not all([game_id, player_id, city_name]):
        return jsonify({"status": "error", "message": "Missing required fields"}), 400

    game = _get_game_or_load(game_id)
    if not game:
        return jsonify({"status": "error", "message": "Game not found"}), 404

    card = _get_card_from_game(game, int(card_id)) if card_id is not None else None
    player = _get_player_from_game(game, int(player_id))

    if not player:
        return jsonify({"status": "error", "message": "Player not in game"}), 404

    result = game.build_research_station_player(int(player_id), city_name, card)
    status = result.get("status", 500)

    if status == 200:
        socketio.emit("player:built_station", {"player_id": player_id, "city": city_name}, room=game_id)
        _emit_log(game_id, f"{player.name} построил исследовательскую станцию в {city_name}")

    return jsonify(result), status

@api.post("/player/trade-card")
def post_player_trade_card() -> Any:
    """Trade (share knowledge) between players.
    
    
    Expected JSON:
    {
    "game_id": str,
    "from_player_id": str,
    "to_player_id": str,
    "card_id": str,
    "city": str | null # optional; classical rules often require same city
    }
    """
    data = request.get_json() or {}
    game_id = data.get("game_id")
    from_player_id = data.get("from_player_id")
    to_player_id = data.get("to_player_id")
    card_id = data.get("card_id")

    if not all([game_id, from_player_id, to_player_id, card_id]):
        return jsonify({"status": "error", "message": "Missing required fields"}), 400

    game = _get_game_or_load(game_id)
    if not game:
        return jsonify({"status": "error", "message": "Game not found"}), 404

    from_player = _get_player_from_game(game, int(from_player_id))
    to_player = _get_player_from_game(game, int(to_player_id))
    card = _get_card_from_game(game, int(card_id))

    if not from_player or not to_player:
        return jsonify({"status": "error", "message": "Player not in game"}), 404
    if not card:
        return jsonify({"status": "error", "message": "Card not found"}), 404

    result = game.trade_card_player(int(from_player_id), int(to_player_id), card)
    status = result.get("status", 500)

    if status == 200:
        socketio.emit(
            "player:traded_card",
            {"from": from_player_id, "to": to_player_id, "card_id": card_id},
            room=game_id,
        )
        _emit_log(game_id, f"{from_player.name} передал карту {card.name} игроку {to_player.name}")

    return jsonify(result), status

@api.post("/player/discover-cure")
def post_player_discover_cure() -> Any:
    """Discover a cure for a disease color.
    
    
    Expected JSON:
    {
    "game_id": str,
    "player_id": str,
    "color": str, # e.g., "blue", "yellow", "black", "red"
    "card_ids": list[str] # typically 4/5 cards by rules; soft-checked here
    }
    """
    data = request.get_json() or {}
    game_id = data.get("game_id")
    player_id = data.get("player_id")
    color_name = (data.get("color") or "").lower()
    card_ids = data.get("card_ids") or []

    if not all([game_id, player_id, color_name, card_ids]):
        return jsonify({"status": "error", "message": "Missing required fields"}), 400

    game = _get_game_or_load(game_id)
    if not game:
        return jsonify({"status": "error", "message": "Game not found"}), 404

    from data.enums import ColorType

    try:
        color_type = getattr(ColorType, color_name)
    except Exception:
        return jsonify({"status": "error", "message": "Invalid color"}), 400

    try:
        cards = [_get_card_from_game(game, int(c_id)) for c_id in card_ids]
    except Exception:
        return jsonify({"status": "error", "message": "Invalid card id"}), 400

    if any(card is None for card in cards):
        return jsonify({"status": "error", "message": "Card not found"}), 404

    player = _get_player_from_game(game, int(player_id))
    if not player:
        return jsonify({"status": "error", "message": "Player not in game"}), 404

    result = game.discover_cure_player(int(player_id), color_type, cards)  # type: ignore[arg-type]
    status = result.get("status", 500)

    if status == 200:
        socketio.emit("player:discovered_cure", {"player_id": player_id, "color": color_name}, room=game_id)
        _emit_log(game_id, f"{player.name} открыл лекарство от {color_name}")

    return jsonify(result), status

@api.post("/player/discard-card")
def post_player_discard_card() -> Any:
    """Discard a card from the player's hand.
    
    
    Expected JSON:
    {
    "game_id": str,
    "player_id": str,
    "card_id": str
    }
    """
    data = request.get_json() or {}
    game_id = data.get("game_id")
    player_id = data.get("player_id")
    card_id = data.get("card_id")

    if not all([game_id, player_id, card_id]):
        return jsonify({"status": "error", "message": "Missing required fields"}), 400

    game = _get_game_or_load(game_id)
    if not game:
        return jsonify({"status": "error", "message": "Game not found"}), 404

    card = _get_card_from_game(game, int(card_id))
    if not card:
        return jsonify({"status": "error", "message": "Card not found"}), 404

    card.player_owner = None
    card.use()

    _emit_log(game_id, f"Карта {card.name} сброшена", {"player_id": player_id})

    return jsonify({"status": "ok", "message": "Card discarded"}), 200

@api.post("/player/end-action")
def post_player_end_action() -> Any:
    """Explicitly end a single action (client keeps count up to 4 per turn).
    
    
    Expected JSON:
    {
    "game_id": str,
    "player_id": str,
    "action_counter": int | null # client-side count; server may verify
    }
    """
    data = request.get_json() or {}
    game_id = data.get("game_id")

    if not game_id:
        return jsonify({"status": "error", "message": "Missing game_id"}), 400

    game = _get_game_or_load(game_id)
    if not game:
        return jsonify({"status": "error", "message": "Game not found"}), 404

    result = game.notify_turn_ended()
    status = result.get("status", 500)

    if status == 200:
        notify_turn_ended(game_id, data.get("player_id"), None)
        _emit_log(game_id, "Ход завершён")

    return jsonify(result), status

# ------------------------------
# Socket.IO — PlayerModel action events (namespace=/)
# ------------------------------


NAMESPACE = "/"

@socketio.on("player:move", namespace=NAMESPACE)
def sio_player_move(data) -> None:
    """Handle real-time player movement."""
    code = data.get("game_code")
    player_id = data.get("player_id")
    to_city_name = data.get("to_city")
    card_id = data.get("card_id")

    if not all([code, player_id, to_city_name]):
        emit("player:move:error", {"message": "Missing required fields"}, room=request.sid)
        return

    game = _get_game_or_load(code)
    if not game:
        emit("player:move:error", {"message": f"Session {code} not found"}, room=request.sid)
        return

    player = _get_player_from_game(game, int(player_id))
    card = _get_card_from_game(game, int(card_id)) if card_id is not None else None

    if not player:
        emit("player:move:error", {"message": "Player not in game"}, room=request.sid)
        return

    try:
        result = game.move_player(int(player_id), to_city_name, card)
        status = result.get("status", 500)
    except Exception as e:
        print(f"[sio_move] {e}")
        emit("player:move:error", {"message": "Internal error"}, room=request.sid)
        return

    if status == 200:
        notify_player_moved(code, player, to_city_name)
        emit("player:moved:ack", {"player_id": player_id, "new_city": to_city_name}, room=request.sid)
    else:
        emit("player:move:error", {"message": result.get("message", "Move failed")}, room=request.sid)

@socketio.on("player:use_event", namespace=NAMESPACE)
def sio_player_use_event(data: Dict[str, Any]) -> None:
    game_id = data.get("game_id")
    player_id = data.get("player_id")
    card_id = data.get("event_card_id")

    if not all([game_id, player_id, card_id]):
        emit("player:use_event:error", {"message": "Missing required fields"}, room=request.sid)
        return

    game = _get_game_or_load(game_id)
    card = _get_card_from_game(game, int(card_id)) if game else None
    player = _get_player_from_game(game, int(player_id)) if game else None

    if not game:
        emit("player:use_event:error", {"message": "Game not found"}, room=request.sid)
        return
    if not player or not card:
        emit("player:use_event:error", {"message": "Player or card not found"}, room=request.sid)
        return

    result = game.use_event_player(int(player_id), card)
    status = result.get("status", 500)
    if status == 200:
        socketio.emit("player:used_event", {"player_id": player_id, "card_id": card_id}, room=game_id)
        _emit_log(game_id, f"{player.name} использовал карту события {card.name}")
    else:
        emit("player:use_event:error", {"message": result.get("message")}, room=request.sid)

@socketio.on("player:build_station", namespace=NAMESPACE)
def sio_player_build_station(data: Dict[str, Any]) -> None:
    game_id = data.get("game_id")
    player_id = data.get("player_id")
    city_name = data.get("city")
    card_id = data.get("card_id")

    if not all([game_id, player_id, city_name]):
        emit("player:build_station:error", {"message": "Missing required fields"}, room=request.sid)
        return

    game = _get_game_or_load(game_id)
    card = _get_card_from_game(game, int(card_id)) if game and card_id is not None else None
    player = _get_player_from_game(game, int(player_id)) if game else None

    if not game or not player:
        emit("player:build_station:error", {"message": "Game or player not found"}, room=request.sid)
        return

    result = game.build_research_station_player(int(player_id), city_name, card)
    status = result.get("status", 500)
    if status == 200:
        socketio.emit("player:built_station", {"player_id": player_id, "city": city_name}, room=game_id)
        _emit_log(game_id, f"{player.name} построил исследовательскую станцию в {city_name}")
    else:
        emit("player:build_station:error", {"message": result.get("message")}, room=request.sid)

@socketio.on("player:trade_card", namespace=NAMESPACE)
def sio_player_trade_card(data: Dict[str, Any]) -> None:
    game_id = data.get("game_id")
    from_player_id = data.get("from_player_id")
    to_player_id = data.get("to_player_id")
    card_id = data.get("card_id")

    if not all([game_id, from_player_id, to_player_id, card_id]):
        emit("player:trade_card:error", {"message": "Missing required fields"}, room=request.sid)
        return

    game = _get_game_or_load(game_id)
    if not game:
        emit("player:trade_card:error", {"message": "Game not found"}, room=request.sid)
        return

    from_player = _get_player_from_game(game, int(from_player_id))
    to_player = _get_player_from_game(game, int(to_player_id))
    card = _get_card_from_game(game, int(card_id))

    if not from_player or not to_player or not card:
        emit("player:trade_card:error", {"message": "Invalid payload"}, room=request.sid)
        return

    result = game.trade_card_player(int(from_player_id), int(to_player_id), card)
    status = result.get("status", 500)
    if status == 200:
        socketio.emit(
            "player:traded_card",
            {"from": from_player_id, "to": to_player_id, "card_id": card_id},
            room=game_id,
        )
        _emit_log(game_id, f"{from_player.name} передал карту {card.name} игроку {to_player.name}")
    else:
        emit("player:trade_card:error", {"message": result.get("message")}, room=request.sid)

@socketio.on("player:discover_cure", namespace=NAMESPACE)
def sio_player_discover_cure(data: Dict[str, Any]) -> None:
    game_id = data.get("game_id")
    player_id = data.get("player_id")
    color_name = (data.get("color") or "").lower()
    card_ids = data.get("card_ids") or []

    if not all([game_id, player_id, color_name, card_ids]):
        emit("player:discover_cure:error", {"message": "Missing required fields"}, room=request.sid)
        return

    game = _get_game_or_load(game_id)
    if not game:
        emit("player:discover_cure:error", {"message": "Game not found"}, room=request.sid)
        return

    from data.enums import ColorType
    try:
        color_type = getattr(ColorType, color_name)
    except Exception:
        emit("player:discover_cure:error", {"message": "Invalid color"}, room=request.sid)
        return

    try:
        cards = [_get_card_from_game(game, int(c_id)) for c_id in card_ids]
    except Exception:
        emit("player:discover_cure:error", {"message": "Invalid cards"}, room=request.sid)
        return

    if any(card is None for card in cards):
        emit("player:discover_cure:error", {"message": "Card not found"}, room=request.sid)
        return

    player = _get_player_from_game(game, int(player_id))
    if not player:
        emit("player:discover_cure:error", {"message": "Player not in game"}, room=request.sid)
        return

    result = game.discover_cure_player(int(player_id), color_type, cards)  # type: ignore[arg-type]
    status = result.get("status", 500)

    if status == 200:
        socketio.emit("player:discovered_cure", {"player_id": player_id, "color": color_name}, room=game_id)
        _emit_log(game_id, f"{player.name} открыл лекарство от {color_name}")
    else:
        emit("player:discover_cure:error", {"message": result.get("message")}, room=request.sid)

@socketio.on("player:discard_card", namespace=NAMESPACE)
def sio_player_discard_card(data: Dict[str, Any]) -> None:
    game_id = data.get("game_id")
    player_id = data.get("player_id")
    card_id = data.get("card_id")

    if not all([game_id, player_id, card_id]):
        emit("player:discard_card:error", {"message": "Missing required fields"}, room=request.sid)
        return

    game = _get_game_or_load(game_id)
    card = _get_card_from_game(game, int(card_id)) if game else None

    if not game or not card:
        emit("player:discard_card:error", {"message": "Game or card not found"}, room=request.sid)
        return

    card.player_owner = None
    card.use()
    _emit_log(game_id, f"Карта {card.name} сброшена", {"player_id": player_id})
    emit("player:discarded_card", {"card_id": card_id}, room=game_id)

@socketio.on("player:end_action", namespace=NAMESPACE)
def sio_player_end_action(data: Dict[str, Any]) -> None:
    game_id = data.get("game_id")
    if not game_id:
        emit("player:end_action:error", {"message": "Missing game_id"}, room=request.sid)
        return

    game = _get_game_or_load(game_id)
    if not game:
        emit("player:end_action:error", {"message": "Game not found"}, room=request.sid)
        return

    result = game.notify_turn_ended()
    status = result.get("status", 500)
    if status == 200:
        notify_turn_ended(game_id, data.get("player_id"), None)
    else:
        emit("player:end_action:error", {"message": result.get("message")}, room=request.sid)

# ------------------------------
# Server-originated game lifecycle notifications
# ------------------------------

def notify_player_moved(game_code: str, player: PlayerModel, new_city_name: str) -> None:
    """
    Notify all clients in the same game room that a player has moved.
    """
    socketio.emit(
        "player:moved",
        {
            "player_id": player.id,
            "new_city": new_city_name,
            "actions_left": player.actions_left
        },
        room=game_code,
        namespace=NAMESPACE
    )

def notify_turn_ended(game_id: str, player_id: str, next_player_id: str) -> None:
    """Broadcast end of the current player's turn.
    Payload suggestion:
    {
    "game_id": str,
    "ended_player_id": str,
    "next_player_id": str,
    "turn_index": int | null
    }
    Emits: "server:turn_ended" to /game and /host.
    """
    payload = {
        "game_id": game_id,
        "ended_player_id": player_id,
        "next_player_id": next_player_id,
    }
    socketio.emit(SERVER_EVENTS["turn_ended"], payload, room=game_id, namespace=NAMESPACE)
    socketio.emit(SERVER_EVENTS["turn_ended"], payload, room=game_id)
    _emit_log(game_id, "Ход завершён", payload)

def notify_player_drew_cards(game_id: str, player_id: str, card_ids: list[str], reshuffle_discard: bool | None = None) -> None:
    """Broadcast that a player drew cards from the player deck.
    Payload suggestion:
    {
    "game_id": str,
    "player_id": str,
    "card_ids": list[str], # may be partially hidden to other players in UI
    "reshuffle_discard": bool | null # e.g., after epidemic intensify step
    }
    Emits: "server:player_drew_cards".
    """
    payload = {
        "game_id": game_id,
        "player_id": player_id,
        "card_ids": card_ids,
        "reshuffle_discard": reshuffle_discard,
    }
    socketio.emit(SERVER_EVENTS["player_drew_cards"], payload, room=game_id, namespace=NAMESPACE)
    _emit_log(game_id, f"Игрок {player_id} добрал карты", payload)

def notify_disease_spread(game_id: str, city: str, color: str, cubes_added: int, chain: list[dict] | None = None) -> None:
    """Broadcast disease spread in a city (normal infection step).
    Payload suggestion:
    {
    "game_id": str,
    "city": str,
    "color": str,
    "cubes_added": int,
    "chain": [ {"city": str, "cubes": int} ] | null # optional detailed trace
    }
    Emits: "server:disease_spread".
    """
    payload = {
        "game_id": game_id,
        "city": city,
        "color": color,
        "cubes_added": cubes_added,
        "chain": chain,
    }
    socketio.emit(SERVER_EVENTS["disease_spread"], payload, room=game_id, namespace=NAMESPACE)
    _emit_log(game_id, f"Инфекция распространяется в {city}", payload)

def notify_epidemic(game_id: str, city: str, color: str, infection_rate: int, intensify: bool) -> None:
    """Broadcast epidemic event (draw bottom card, increase rate, intensify).
    Payload suggestion:
    {
    "game_id": str,
    "city": str,
    "color": str,
    "infection_rate": int,
    "intensify": bool
    }
    Emits: "server:epidemic".
    """
    payload = {
        "game_id": game_id,
        "city": city,
        "color": color,
        "infection_rate": infection_rate,
        "intensify": intensify,
    }
    socketio.emit(SERVER_EVENTS["epidemic"], payload, room=game_id, namespace=NAMESPACE)
    _emit_log(game_id, f"Эпидемия в {city}", payload)

def notify_outbreak(game_id: str, origin_city: str, color: str, affected: list[str], outbreak_count: int) -> None:
    """Broadcast an outbreak and list affected cities.
    Payload suggestion:
    {
    "game_id": str,
    "origin_city": str,
    "color": str,
    "affected": list[str],
    "outbreak_count": int
    }
    Emits: "server:outbreak".
    """
    payload = {
        "game_id": game_id,
        "origin_city": origin_city,
        "color": color,
        "affected": affected,
        "outbreak_count": outbreak_count,
    }
    socketio.emit(SERVER_EVENTS["outbreak"], payload, room=game_id, namespace=NAMESPACE)
    _emit_log(game_id, f"Вспышка болезни в {origin_city}", payload)

def notify_disease_cured(game_id: str, color: str, eradicated: bool) -> None:
    """Broadcast that a disease was cured (and whether it is eradicated).
    Payload suggestion:
    {
    "game_id": str,
    "color": str,
    "eradicated": bool
    }
    Emits: "server:disease_cured".
    """
    payload = {"game_id": game_id, "color": color, "eradicated": eradicated}
    socketio.emit(SERVER_EVENTS["disease_cured"], payload, room=game_id, namespace=NAMESPACE)
    _emit_log(game_id, f"Лекарство от {color} {'уничтожило болезнь' if eradicated else 'создано'}", payload)

def notify_game_over(game_id: str, outcome: str, reason: str | None = None, stats: dict | None = None) -> None:
    """Broadcast game end.
    Payload suggestion:
    {
    "game_id": str,
    "outcome": "victory" | "defeat",
    "reason": str | null, # e.g., outbreaks_limit, player_deck_empty, cubes_exhausted
    "stats": dict | null
    }
    Emits: "server:game_over".
    """
    payload = {
        "game_id": game_id,
        "outcome": outcome,
        "reason": reason,
        "stats": stats,
    }
    socketio.emit(SERVER_EVENTS["game_over"], payload, room=game_id, namespace=NAMESPACE)
    _emit_log(game_id, f"Игра завершена ({outcome})", payload)


SERVER_EVENTS = {
    "turn_ended": "server:turn_ended",
    "player_drew_cards": "server:player_drew_cards",
    "disease_spread": "server:disease_spread",
    "epidemic": "server:epidemic",
    "outbreak": "server:outbreak",
    "disease_cured": "server:disease_cured",
    "game_over": "server:game_over",
}
