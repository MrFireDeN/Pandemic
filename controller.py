from flask import Blueprint, jsonify, request
from eng import db, socketio
from models import GameSession, Player
from flask_socketio import emit, join_room
import secrets

from typing import Any, Dict

api = Blueprint("api", __name__)

@api.route("/health")
def health():
    return jsonify({"status": "ok"})

@api.post("/host/create")
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

# ------------------------------
# REST endpoints — Player actions
# ------------------------------

@api.post("/player/move")
def post_player_move() -> Any:
    pass
    """Move a pawn from one city to another.

    Expected JSON:
    {
    "game_id": str,
    "player_id": str,
    "from_city": str, # current location (optional if server tracks)
    "to_city": str,
    "card_id": str | null, # optional; client may omit per "soft rules"
    "transport": str | null # e.g., "drive", "direct", "charter", "shuttle"
    }
    """

@api.post("/player/use-event")
def post_player_use_event() -> Any:
    pass
    """Use an event card.

    Expected JSON:
    {
    "game_id": str,
    "player_id": str,
    "event_card_id": str,
    "payload": dict | null # event-specific arguments (city, target, etc.)
    }
    """

@api.post("/player/build-research-station")
def post_player_build_research_station() -> Any:
    pass
    """Build a research station in a city.
    
    
    Expected JSON:
    {
    "game_id": str,
    "player_id": str,
    "city": str,
    "card_id": str | null # optional per "soft rules"
    }
    """

@api.post("/player/trade-card")
def post_player_trade_card() -> Any:
    pass
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

@api.post("/player/discover-cure")
def post_player_discover_cure() -> Any:
    pass
    """Discover a cure for a disease color.
    
    
    Expected JSON:
    {
    "game_id": str,
    "player_id": str,
    "color": str, # e.g., "blue", "yellow", "black", "red"
    "card_ids": list[str] # typically 4/5 cards by rules; soft-checked here
    }
    """

@api.post("/player/discard-card")
def post_player_discard_card() -> Any:
    pass
    """Discard a card from the player's hand.
    
    
    Expected JSON:
    {
    "game_id": str,
    "player_id": str,
    "card_id": str
    }
    """

@api.post("/player/end-action")
def post_player_end_action() -> Any:
    pass
    """Explicitly end a single action (client keeps count up to 4 per turn).
    
    
    Expected JSON:
    {
    "game_id": str,
    "player_id": str,
    "action_counter": int | null # client-side count; server may verify
    }
    """

# ------------------------------
# Socket.IO — Player action events (namespace=/game)
# ------------------------------


NAMESPACE = "/game"

@socketio.on("player:move", namespace=NAMESPACE)
def sio_player_move(data: Dict[str, Any]) -> None:
    pass

@socketio.on("player:use_event", namespace=NAMESPACE)
def sio_player_use_event(data: Dict[str, Any]) -> None:
    pass

@socketio.on("player:build_station", namespace=NAMESPACE)
def sio_player_build_station(data: Dict[str, Any]) -> None:
    pass

@socketio.on("player:trade_card", namespace=NAMESPACE)
def sio_player_trade_card(data: Dict[str, Any]) -> None:
    pass

@socketio.on("player:discover_cure", namespace=NAMESPACE)
def sio_player_discover_cure(data: Dict[str, Any]) -> None:
    pass

@socketio.on("player:discard_card", namespace=NAMESPACE)
def sio_player_discard_card(data: Dict[str, Any]) -> None:
    pass

@socketio.on("player:end_action", namespace=NAMESPACE)
def sio_player_end_action(data: Dict[str, Any]) -> None:
    pass

# ------------------------------
# Server-originated game lifecycle notifications
# ------------------------------

def notify_turn_ended(game_id: str, player_id: str, next_player_id: str) -> None:
    pass
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

def notify_player_drew_cards(game_id: str, player_id: str, card_ids: list[str], reshuffle_discard: bool | None = None) -> None:
    pass
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




def notify_disease_spread(game_id: str, city: str, color: str, cubes_added: int, chain: list[dict] | None = None) -> None:
    pass
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



def notify_epidemic(game_id: str, city: str, color: str, infection_rate: int, intensify: bool) -> None:
    pass
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




def notify_outbreak(game_id: str, origin_city: str, color: str, affected: list[str], outbreak_count: int) -> None:
    pass
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

def notify_disease_cured(game_id: str, color: str, eradicated: bool) -> None:
    pass
    """Broadcast that a disease was cured (and whether it is eradicated).
    Payload suggestion:
    {
    "game_id": str,
    "color": str,
    "eradicated": bool
    }
    Emits: "server:disease_cured".
    """

def notify_game_over(game_id: str, outcome: str, reason: str | None = None, stats: dict | None = None) -> None:
    pass
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


SERVER_EVENTS = {
    "turn_ended": "server:turn_ended",
    "player_drew_cards": "server:player_drew_cards",
    "disease_spread": "server:disease_spread",
    "epidemic": "server:epidemic",
    "outbreak": "server:outbreak",
    "disease_cured": "server:disease_cured",
    "game_over": "server:game_over",
}