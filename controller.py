from flask import Blueprint, request, jsonify, render_template, current_app
from flask_socketio import emit, join_room, leave_room
from eng import socketio, db
from game import PandemicGame, SESSIONS, Observer
from data.enums import ColorType, RoleType, CardType
from data.repo import GameRepository
import random
import string


# Observer для передачи событий через сокеты
class SocketObserver(Observer):
    def __init__(self, game_code: str):
        self.game_code = game_code
    
    def update(self, message):
        """Передает события игры через сокеты"""
        try:
            event_name = message.get("event", "game_event")
            socketio.emit(event_name, message, room=self.game_code)
        except Exception as e:
            print(f"Error in SocketObserver.update: {e}")


# Blueprint для API
api = Blueprint('api', __name__)


def get_game(code: str) -> PandemicGame | None:
    """Получить игру по коду"""
    if not code:
        print("Error: get_game called with empty code")
        return None
    
    print(f"Getting game with code: {code}")
    
    # Сначала проверяем в памяти
    game = SESSIONS.get_session(code)
    if game is not None:
        print(f"Game {code} found in SESSIONS")
        return game
    
    # Попробуем загрузить из БД
    print(f"Game {code} not in SESSIONS, trying to load from DB...")
    try:
        # Используем current_app для получения контекста приложения
        from flask import has_app_context
        if has_app_context():
            game = GameRepository.load_game(code)
            if game:
                print(f"Game {code} loaded from DB successfully")
                SESSIONS.add_session(game)
                # Добавляем observer
                observer = SocketObserver(code)
                game.add_observer(observer)
                return game
            else:
                print(f"Game {code} not found in DB")
        else:
            # Если нет контекста, попробуем использовать current_app напрямую
            try:
                app = current_app._get_current_object()
                with app.app_context():
                    game = GameRepository.load_game(code)
                    if game:
                        print(f"Game {code} loaded from DB successfully (with app context)")
                        SESSIONS.add_session(game)
                        observer = SocketObserver(code)
                        game.add_observer(observer)
                        return game
            except:
                print(f"No Flask app context available for loading game {code}")
    except Exception as e:
        print(f"Error loading game {code} from DB: {e}")
        import traceback
        traceback.print_exc()
    
    return None


def serialize_player(player):
    """Сериализация игрока для JSON"""
    return {
        "id": player.id,
        "name": player.name,
        "role": player.role.name if hasattr(player.role, 'name') else str(player.role),
        "position": player.pos.name if player.pos else None,
        "actions_left": player.actions_left
    }


def serialize_city(city):
    """Сериализация города для JSON"""
    infections = {}
    for color in ColorType:
        infections[color.name] = city.infection_cubes.get(color, 0)
    
    return {
        "id": city.id,
        "name": city.name,
        "color": city.color.name if hasattr(city.color, 'name') else str(city.color),
        "population": city.population,
        "has_research_station": city.has_station,
        "infections": infections
    }


def serialize_card(card):
    """Сериализация карты для JSON"""
    return {
        "id": card.id,
        "name": card.name,
        "type": card.type.name if hasattr(card.type, 'name') else str(card.type),
        "owner_id": card.player_owner.id if card.player_owner else None
    }


def serialize_game_state(game: PandemicGame):
    """Сериализация состояния игры для JSON"""
    players = [serialize_player(p) for p in game.players]
    
    cities = []
    if game.cities:
        for city in game.cities.cities_by_name.values():
            cities.append(serialize_city(city))
    
    board_data = {
        "turn_order": game.board.turn_order,
        "outbreak_indicator": game.board.outbreak_indicator,
        "infection_indicator": game.board.infection_indicator,
        "cubes_per_color": {color.name: count for color, count in game.board.cubes_per_color.items()},
        "vaccines_state": {color.name: state for color, state in game.board.vaccines_state.items()},
        "is_game_over": game.board.is_game_over
    }
    
    return {
        "code": game.code,
        "phase": game.phase,
        "difficult": game.difficult.name if hasattr(game.difficult, 'name') else str(game.difficult),
        "players": players,
        "cities": cities,
        "board": board_data,
        "current_player": players[game.board.turn_order] if game.players else None
    }


# API Endpoints
@api.route('/health', methods=['GET'])
def health():
    """Проверка доступности сервера"""
    return jsonify({"status": "ok", "message": "Server is running"})


@api.route('/host/create', methods=['POST'])
def create_host():
    """Создать игровую комнату"""
    try:
        # Генерируем случайный код из 4 символов
        code = ''.join(random.choices(string.ascii_uppercase, k=4))
        
        # Проверяем, что такого кода нет
        while SESSIONS.get_session(code) is not None:
            code = ''.join(random.choices(string.ascii_uppercase, k=4))
        
        game = SESSIONS.create_session(code)
        
        # Добавляем observer
        observer = SocketObserver(code)
        game.add_observer(observer)
        
        # Сохраняем в БД
        GameRepository.save_game(game)
        
        return jsonify({"status": "ok", "code": code})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@api.route('/game/<code>/state', methods=['GET'])
def get_game_state(code):
    """Получить состояние игры"""
    try:
        game = get_game(code)
        if game is None:
            # Попробуем создать игру, если её нет (может быть она еще не была создана)
            print(f"Game {code} not found, trying to create it...")
            try:
                game = SESSIONS.create_session(code)
                observer = SocketObserver(code)
                game.add_observer(observer)
                GameRepository.save_game(game)
                print(f"Game {code} created successfully")
            except Exception as e:
                print(f"Error creating game {code}: {e}")
                return jsonify({"status": "error", "message": "Game not found and could not be created"}), 404
        
        return jsonify({"status": "ok", "data": serialize_game_state(game)})
    except Exception as e:
        print(f"Error in get_game_state: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500


@api.route('/game/<code>/players', methods=['GET'])
def get_players(code):
    """Получить список игроков"""
    try:
        game = get_game(code)
        if game is None:
            return jsonify({"status": "error", "message": "Game not found"}), 404
        
        players = [serialize_player(p) for p in game.players]
        return jsonify({"status": "ok", "data": players})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@api.route('/game/<code>/cities', methods=['GET'])
def get_cities(code):
    """Получить список городов"""
    try:
        game = get_game(code)
        if game is None:
            return jsonify({"status": "error", "message": "Game not found"}), 404
        
        cities = []
        if game.cities:
            for city in game.cities.cities_by_name.values():
                cities.append(serialize_city(city))
        
        return jsonify({"status": "ok", "data": cities})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@api.route('/game/<code>/move', methods=['POST'])
def move_player(code):
    """Переместить игрока"""
    try:
        game = get_game(code)
        if game is None:
            return jsonify({"status": "error", "message": "Game not found"}), 404
        
        data = request.get_json()
        player_id = data.get('player_id')
        to_city = data.get('to_city')
        
        if not player_id or not to_city:
            return jsonify({"status": "error", "message": "Missing parameters"}), 400
        
        result = game.move_player(int(player_id), to_city)
        
        # Всегда возвращаем состояние игры, даже при ошибке
        game_state = serialize_game_state(game)
        if result.get("status") == 200:
            return jsonify({"status": "ok", "data": game_state})
        else:
            return jsonify({"status": "error", "message": result.get("message", "Unknown error"), "data": game_state}), result.get("status", 500)
    except Exception as e:
        # При ошибке все равно пытаемся вернуть состояние игры
        try:
            game = get_game(code)
            if game:
                game_state = serialize_game_state(game)
                return jsonify({"status": "error", "message": str(e), "data": game_state}), 500
        except:
            pass
        return jsonify({"status": "error", "message": str(e)}), 500


@api.route('/game/<code>/cure', methods=['POST'])
def cure_city(code):
    """Вылечить город"""
    try:
        game = get_game(code)
        if game is None:
            return jsonify({"status": "error", "message": "Game not found"}), 404
        
        data = request.get_json()
        player_id = data.get('player_id')
        city_name = data.get('city_name')
        color_str = data.get('color')
        
        if not player_id or not city_name or not color_str:
            return jsonify({"status": "error", "message": "Missing parameters"}), 400
        
        try:
            color = ColorType[color_str.lower()]
        except (KeyError, AttributeError):
            return jsonify({"status": "error", "message": "Invalid color"}), 400
        
        result = game.cure_city_player(int(player_id), city_name, color)
        
        # Всегда возвращаем состояние игры, даже при ошибке
        game_state = serialize_game_state(game)
        if result.get("status") == 200:
            return jsonify({"status": "ok", "data": game_state})
        else:
            return jsonify({"status": "error", "message": result.get("message", "Unknown error"), "data": game_state}), result.get("status", 500)
    except Exception as e:
        # При ошибке все равно пытаемся вернуть состояние игры
        try:
            game = get_game(code)
            if game:
                game_state = serialize_game_state(game)
                return jsonify({"status": "error", "message": str(e), "data": game_state}), 500
        except:
            pass
        return jsonify({"status": "error", "message": str(e)}), 500


@api.route('/game/<code>/build_station', methods=['POST'])
def build_station(code):
    """Построить исследовательскую станцию"""
    try:
        game = get_game(code)
        if game is None:
            return jsonify({"status": "error", "message": "Game not found"}), 404
        
        data = request.get_json()
        player_id = data.get('player_id')
        city_name = data.get('city_name')
        card_id = data.get('card_id')
        
        if not player_id or not city_name:
            return jsonify({"status": "error", "message": "Missing parameters"}), 400
        
        # Находим карту
        card = None
        if card_id:
            for c in game.deck_cards.draw_pile + game.deck_cards.discard_pile:
                if c.id == card_id:
                    card = c
                    break
        
        result = game.build_research_station_player(int(player_id), city_name, card)
        
        # Всегда возвращаем состояние игры, даже при ошибке
        game_state = serialize_game_state(game)
        if result.get("status") == 200:
            return jsonify({"status": "ok", "data": game_state})
        else:
            return jsonify({"status": "error", "message": result.get("message", "Unknown error"), "data": game_state}), result.get("status", 500)
    except Exception as e:
        # При ошибке все равно пытаемся вернуть состояние игры
        try:
            game = get_game(code)
            if game:
                game_state = serialize_game_state(game)
                return jsonify({"status": "error", "message": str(e), "data": game_state}), 500
        except:
            pass
        return jsonify({"status": "error", "message": str(e)}), 500


@api.route('/game/<code>/trade_card', methods=['POST'])
def trade_card(code):
    """Обменять карту"""
    try:
        game = get_game(code)
        if game is None:
            return jsonify({"status": "error", "message": "Game not found"}), 404
        
        data = request.get_json()
        from_player_id = data.get('from_player_id')
        to_player_id = data.get('to_player_id')
        card_id = data.get('card_id')
        
        if not from_player_id or not to_player_id or not card_id:
            return jsonify({"status": "error", "message": "Missing parameters"}), 400
        
        # Находим карту
        card = None
        for c in game.deck_cards.draw_pile + game.deck_cards.discard_pile:
            if c.id == card_id:
                card = c
                break
        
        if card is None:
            return jsonify({"status": "error", "message": "Card not found"}), 404
        
        result = game.trade_card_player(int(from_player_id), int(to_player_id), card)
        
        # Всегда возвращаем состояние игры, даже при ошибке
        game_state = serialize_game_state(game)
        if result.get("status") == 200:
            return jsonify({"status": "ok", "data": game_state})
        else:
            return jsonify({"status": "error", "message": result.get("message", "Unknown error"), "data": game_state}), result.get("status", 500)
    except Exception as e:
        # При ошибке все равно пытаемся вернуть состояние игры
        try:
            game = get_game(code)
            if game:
                game_state = serialize_game_state(game)
                return jsonify({"status": "error", "message": str(e), "data": game_state}), 500
        except:
            pass
        return jsonify({"status": "error", "message": str(e)}), 500


@api.route('/game/<code>/discover_cure', methods=['POST'])
def discover_cure(code):
    """Открыть лекарство"""
    try:
        game = get_game(code)
        if game is None:
            return jsonify({"status": "error", "message": "Game not found"}), 404
        
        data = request.get_json()
        player_id = data.get('player_id')
        color_str = data.get('color')
        card_ids = data.get('card_ids', [])
        
        if not player_id or not color_str or not card_ids:
            return jsonify({"status": "error", "message": "Missing parameters"}), 400
        
        try:
            color = ColorType[color_str.lower()]
        except (KeyError, AttributeError):
            return jsonify({"status": "error", "message": "Invalid color"}), 400
        
        # Находим карты
        cards = []
        all_cards = game.deck_cards.draw_pile + game.deck_cards.discard_pile
        for card_id in card_ids:
            for c in all_cards:
                if c.id == card_id:
                    cards.append(c)
                    break
        
        result = game.discover_cure_player(int(player_id), color, cards)
        
        # Всегда возвращаем состояние игры, даже при ошибке
        game_state = serialize_game_state(game)
        if result.get("status") == 200:
            return jsonify({"status": "ok", "data": game_state})
        else:
            return jsonify({"status": "error", "message": result.get("message", "Unknown error"), "data": game_state}), result.get("status", 500)
    except Exception as e:
        # При ошибке все равно пытаемся вернуть состояние игры
        try:
            game = get_game(code)
            if game:
                game_state = serialize_game_state(game)
                return jsonify({"status": "error", "message": str(e), "data": game_state}), 500
        except:
            pass
        return jsonify({"status": "error", "message": str(e)}), 500


@api.route('/game/<code>/end_turn', methods=['POST'])
def end_turn(code):
    """Завершить ход"""
    try:
        game = get_game(code)
        if game is None:
            return jsonify({"status": "error", "message": "Game not found"}), 404
        
        result = game.notify_turn_ended()
        
        # Всегда возвращаем состояние игры, даже при ошибке
        game_state = serialize_game_state(game)
        if result.get("status") == 200:
            return jsonify({"status": "ok", "data": game_state})
        else:
            return jsonify({"status": "error", "message": result.get("message", "Unknown error"), "data": game_state}), result.get("status", 500)
    except Exception as e:
        # При ошибке все равно пытаемся вернуть состояние игры
        try:
            game = get_game(code)
            if game:
                game_state = serialize_game_state(game)
                return jsonify({"status": "error", "message": str(e), "data": game_state}), 500
        except:
            pass
        return jsonify({"status": "error", "message": str(e)}), 500


@api.route('/game/<code>/actions', methods=['GET'])
def get_actions_log(code):
    """Получить лог действий для игры"""
    try:
        from models import MoveLogModel
        logs = MoveLogModel.query.filter_by(game_id=code).order_by(MoveLogModel.id.desc()).limit(100).all()
        
        actions = []
        for log in logs:
            actions.append({
                "id": log.id,
                "player_id": log.player_id,
                "action": log.action,
                "payload": log.payload,
                "timestamp": log.timestamp.isoformat() if log.timestamp else None
            })
        
        return jsonify({"status": "ok", "data": actions})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# Socket Events
@socketio.on('connect')
def handle_connect():
    """Обработка подключения клиента"""
    print(f"Client connected: {request.sid}")


@socketio.on('disconnect')
def handle_disconnect():
    """Обработка отключения клиента"""
    print(f"Client disconnected: {request.sid}")


@socketio.on('host_join')
def handle_host_join(data):
    """Ведущий присоединяется к комнате"""
    try:
        code = data.get('code')
        if not code:
            emit('error', {'message': 'Code is required'})
            return
        
        game = get_game(code)
        if game is None:
            emit('error', {'message': 'Game not found'})
            return
        
        join_room(code)
        emit('host_ready', {'code': code, 'players': [serialize_player(p) for p in game.players]})
    except Exception as e:
        emit('error', {'message': str(e)})


@socketio.on('player_join')
def handle_player_join(data):
    """Игрок присоединяется к комнате"""
    try:
        code = data.get('code')
        name = data.get('name')
        role_id = data.get('role', 1)
        
        if not code or not name:
            emit('error', {'message': 'Code and name are required'})
            return
        
        game = get_game(code)
        if game is None:
            emit('error', {'message': 'Game not found'})
            return
        
        # Проверяем, не добавлен ли уже игрок с таким именем (с учетом регистра и пробелов)
        existing_player = None
        name_normalized = name.strip().lower()
        for p in game.players:
            if p.name and p.name.strip().lower() == name_normalized:
                existing_player = p
                break
        
        if existing_player:
            player_id = existing_player.id
        else:
            # Создаем нового игрока
            player_id = len(game.players) + 1
            game.add_player(player_id, name, role_id)
            GameRepository.save_game(game)
        
        join_room(code)
        
        # Находим игрока
        player = None
        for p in game.players:
            if p.id == player_id:
                player = p
                break
        
        if player:
            player_data = serialize_player(player)
            print(f"Player joined: {player_data}")
            # Отправляем событие player_joined всем в комнате
            emit('player_joined', player_data, room=code)
            # Также отправляем событие конкретному клиенту с его данными
            emit('player_joined', player_data)
        else:
            print(f"Warning: Player not found after creation. player_id={player_id}, players={[p.name for p in game.players]}")
        
        # Отправляем текущее состояние игры
        game_state = serialize_game_state(game)
        emit('game_state', game_state)
        print(f"Game state sent. Players: {[p.get('name') for p in game_state.get('players', [])]}")
    except Exception as e:
        emit('error', {'message': str(e)})


@socketio.on('start_game')
def handle_start_game(data):
    """Начать игру"""
    try:
        code = data.get('code')
        if not code:
            emit('error', {'message': 'Code is required'})
            return
        
        game = get_game(code)
        if game is None:
            emit('error', {'message': 'Game not found'})
            return
        
        result = game.start_game()
        
        if result.get("status") == 200:
            game_state = serialize_game_state(game)
            # Отправляем состояние игры всем в комнате
            emit('game_started', game_state, room=code)
            # Также отправляем отдельное событие game_state для обновления
            emit('game_state', game_state, room=code)
        else:
            emit('error', {'message': result.get("message", "Failed to start game")})
    except Exception as e:
        emit('error', {'message': str(e)})


@socketio.on('player:move')
def handle_player_move(data):
    """Обработка перемещения игрока"""
    try:
        code = data.get('game_code')
        player_id = data.get('player_id')
        to_city = data.get('to_city')
        
        if not code or player_id is None or not to_city:
            emit('error', {'message': 'Missing parameters'})
            return
        
        game = get_game(code)
        if game is None:
            emit('error', {'message': 'Game not found'})
            return
        
        result = game.move_player(int(player_id), to_city)
        
        if result.get("status") == 200:
            # Находим игрока
            player = None
            for p in game.players:
                if p.id == int(player_id):
                    player = p
                    break
            
            emit('player:moved', {
                'player_id': player_id,
                'new_city': to_city,
                'actions_left': player.actions_left if player else 0
            }, room=code)
        else:
            emit('error', {'message': result.get("message", "Failed to move")})
    except Exception as e:
        emit('error', {'message': str(e)})


@socketio.on('player:cure')
def handle_player_cure(data):
    """Обработка лечения города"""
    try:
        code = data.get('game_code')
        player_id = data.get('player_id')
        city_name = data.get('city_name')
        color_str = data.get('color')
        
        if not code or player_id is None or not city_name or not color_str:
            emit('error', {'message': 'Missing parameters'})
            return
        
        game = get_game(code)
        if game is None:
            emit('error', {'message': 'Game not found'})
            return
        
        try:
            color = ColorType[color_str.lower()]
        except (KeyError, AttributeError):
            emit('error', {'message': 'Invalid color'})
            return
        
        result = game.cure_city_player(int(player_id), city_name, color)
        
        if result.get("status") == 200:
            emit('city:cured', {
                'player_id': player_id,
                'city': city_name,
                'color': color_str
            }, room=code)
        else:
            emit('error', {'message': result.get("message", "Failed to cure")})
    except Exception as e:
        emit('error', {'message': str(e)})


@socketio.on('player:end_turn')
def handle_end_turn(data):
    """Обработка завершения хода"""
    try:
        code = data.get('game_code')
        
        if not code:
            emit('error', {'message': 'Code is required'})
            return
        
        game = get_game(code)
        if game is None:
            emit('error', {'message': 'Game not found'})
            return
        
        result = game.notify_turn_ended()
        
        if result.get("status") == 200:
            emit('turn_ended', serialize_game_state(game), room=code)
        else:
            emit('error', {'message': result.get("message", "Failed to end turn")})
    except Exception as e:
        emit('error', {'message': str(e)})


def load_game_sessions(app):
    """Загрузить игровые сессии из БД при старте приложения"""
    try:
        from models import GameSessionModel
        with app.app_context():
            sessions = GameSessionModel.query.all()
            for session in sessions:
                game = GameRepository.load_game(session.code)
                if game:
                    SESSIONS.add_session(game)
                    # Добавляем observer
                    observer = SocketObserver(session.code)
                    game.add_observer(observer)
    except Exception as e:
        print(f"Error loading game sessions: {e}")
