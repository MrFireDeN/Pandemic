import json

from eng import db

from models import (
    ColorEnumDB,
    CardTypeDB,
    GameStatusDB,
    CityModel, 
    CityConnectionModel, 
    RoleModel, 
    EventModel, 
    CardModel, 
    GameSessionModel, 
    GameStateModel, 
    PlayerModel, 
    MoveLogModel, 
    DeckOfCardsModel, 
    DeckOfDiseasesModel, 
    CityStateModel
)

from game import (
    PandemicGame,
    Board,
    PlayerGame,
    CityGame,
    CityGraph,
    CardGame,
    DeckCards,
    DeckDiseases,
    CardType,
    ColorType,
    RoleType,
    GameStatus
)

class GameRepository:
    def __init__(self):
        pass
        
    @staticmethod
    def save_game(game: PandemicGame) -> None:
        """
        Сохраняет игру в базе данных.
        """
        game_session_model = GameSessionModel.query.filter_by(code=game.code).first()
        
        if game_session_model:
            game_session_model.status = game.phase
        else:
            game_session_model = GameSessionModel(code=game.code, status=game.phase)
            db.session.add(game_session_model)
    
        # Save the board
        board_data = game.board
        board_model = GameStateModel.query.filter_by(game_id=game.code).first()
        
        if board_model is None:
            board_model = GameStateModel(game_id=game.code)
            db.session.add(board_model)
            
        board_model.turn_order          = board_data.turn_order
        board_model.outbreak_indicator  = board_data.outbreak_indicator
        board_model.infection_indicator = board_data.infection_indicator

        cubes_per_color = {color.name: count for color, count in board_data.cubes_per_color.items()}
        vaccines_state = {color.name: state for color, state in board_data.vaccines_state.items()}
        
        board_model.cubes_per_color     = json.dumps(cubes_per_color)
        board_model.vaccines_state      = json.dumps(vaccines_state)
    
        # Save the cities
        city_state_models = CityStateModel.query.filter_by(game_id=game.code).all()
        city_state_by_city_id = {m.city_id: m for m in city_state_models}
        
        city_models = CityModel.query.all()
        city_id_by_name = {m.name: m.id for m in city_models}
        
        for city_name, city in game.cities.cities_by_name.items():
            city_id = city_id_by_name.get(city_name)
            if city_id is None:
                raise ValueError(f"Unknown city name '{city_name}' in CityModel table")

            city_state_model = city_state_by_city_id.get(city_id)
            if city_state_model is None:
                city_state_model = CityStateModel(city_id=city_id, game_id=game.code)
                db.session.add(city_state_model)
                city_state_by_city_id[city_id] = city_state_model

            city_state_model.has_station = city.has_station
            city_state_model.red         = city.infection_cubes[ColorType.red]
            city_state_model.yellow      = city.infection_cubes[ColorType.yellow]
            city_state_model.blue        = city.infection_cubes[ColorType.blue]
            city_state_model.black       = city.infection_cubes[ColorType.black]
    
        # Save the players
        player_models = PlayerModel.query.filter_by(game_id=game.code).all()
        players_by_name = {p.name: p for p in player_models}
        
        for player_data in game.players:
            player_model = players_by_name.get(player_data.name)
        
            if player_model is None:
                player_model = PlayerModel(
                    name=player_data.name,
                    game_id=game.code,
                )
                db.session.add(player_model)
                players_by_name[player_data.name] = player_model
                
            city_id = city_id_by_name.get(player_data.pos.name)
            if city_id is None:
                raise ValueError(f"Unknown city name '{player_data.pos.name}' in CityModel table")
        
            player_model.role_id = player_data.role.value
            player_model.position_city_id = city_id
            # Убеждаемся, что actions_left не отрицательный при сохранении
            player_model.actions_left = max(0, player_data.actions_left) if player_data.actions_left is not None else 4

        db.session.flush()
            
        # Save cards
        card_models = CardModel.query.all()
        card_id_by_name = {m.name: m.id for m in card_models}

        # Save deck of player cards
        deck_of_cards_models = DeckOfCardsModel.query.filter_by(game_id=game.code).all()
        card_in_deck_by_card_id = {m.card_id: m for m in deck_of_cards_models}

        player_id_by_name = {name: model.id for name, model in players_by_name.items()}
        
        def update_deck_card(card_data: CardGame, order_index: int, in_game: bool) -> None:
            card_id = card_id_by_name.get(card_data.name)
        
            deck_card_model = card_in_deck_by_card_id.get(card_id)
            if deck_card_model is None:
                deck_card_model = DeckOfCardsModel(
                    game_id=game.code,
                    card_id=card_id,
                )
                db.session.add(deck_card_model)
                card_in_deck_by_card_id[card_id] = deck_card_model

            owner = getattr(card_data, "player_owner", None)
        
            deck_card_model.order_index = order_index
            deck_card_model.in_game = in_game
            deck_card_model.player_id = player_id_by_name.get(owner.name) if owner else None

        for order_index, card_data in enumerate(game.deck_cards.draw_pile):
            update_deck_card(card_data, order_index=order_index, in_game=True)
    
        for order_index, card_data in enumerate(game.deck_cards.discard_pile):
            update_deck_card(card_data, order_index=order_index, in_game=False)

        # Save deck of diseases cards
        deck_of_diseases_models = DeckOfDiseasesModel.query.filter_by(game_id=game.code).all()
        diseases_in_deck_by_city_id = {m.city_id: m for m in deck_of_diseases_models}
        
        def update_deck_diseases(card_data: CardGame, order_index: int, in_game: bool) -> None:
            card_id = card_id_by_name.get(card_data.name)

            deck_diseases_model = diseases_in_deck_by_city_id.get(card_id)
            if deck_diseases_model is None:
                deck_diseases_model = DeckOfDiseasesModel(
                    game_id=game.code,
                    city_id=card_id,
                )
                db.session.add(deck_diseases_model)
                diseases_in_deck_by_city_id[card_id] = deck_diseases_model

            deck_diseases_model.order_index = order_index
            deck_diseases_model.in_game = in_game
        
        
        for order_index, city_data in enumerate(game.deck_diseases.draw_pile):
            update_deck_diseases(city_data, order_index=order_index, in_game=True)
    
        for order_index, city_data in enumerate(game.deck_diseases.discard_pile):
            update_deck_diseases(city_data, order_index=order_index, in_game=False)
    
        db.session.commit()

    @staticmethod
    def load_game(code: str) -> PandemicGame | None:
        """
        Загружает игру по коду из базы данных.
        """
        session = GameSessionModel.query.filter_by(code=code).first()
        if session is None:
            return None

        game = PandemicGame(code=session.code)
        # Конвертируем GameStatusDB enum в строку
        if hasattr(session.status, 'value'):
            game.phase = session.status.value
        elif hasattr(session.status, 'name'):
            game.phase = session.status.name
        else:
            game.phase = str(session.status)

        # Load the board state
        board_model = GameStateModel.query.filter_by(game_id=code).first()
        if board_model:
            board_data = Board(game)
            board_data.turn_order = board_model.turn_order
            board_data.infection_indicator = board_model.infection_indicator
            board_data.outbreak_indicator = board_model.outbreak_indicator

            cubes_raw = json.loads(board_model.cubes_per_color) if board_model.cubes_per_color else {}
            vaccines_raw = json.loads(board_model.vaccines_state) if board_model.vaccines_state else {}

            def normalize_color_dict(raw: dict, default_value):
                result = {}
                for color in (ColorType.red, ColorType.yellow, ColorType.blue, ColorType.black):
                    result[color] = raw.get(color.name, default_value)
                    
                return result
            
            board_data.cubes_per_color = normalize_color_dict(cubes_raw, 0)
            board_data.vaccines_state = normalize_color_dict(vaccines_raw, 0)
            
            game.board = board_data
        else:
            print(f"Board data for game {code} not found.")

        #  Load city states
        city_models = CityModel.query.all()
        city_state_models = CityStateModel.query.filter_by(game_id=code).all()
        
        city_name_by_id = {m.id: m.name for m in city_models}
        
        for city_state in city_state_models:
            city_name = city_name_by_id.get(city_state.city_id)
            city = game.cities.get_city_by_name(city_name)
            
            if city:
                city.has_station = city_state.has_station
                city.infection_cubes[ColorType.red] = city_state.red
                city.infection_cubes[ColorType.yellow] = city_state.yellow
                city.infection_cubes[ColorType.blue] = city_state.blue
                city.infection_cubes[ColorType.black] = city_state.black

        # Load the player_models
        player_models = PlayerModel.query.filter_by(game_id=code).all()
        player_by_id = {}
        
        for player_model in player_models:
            city_name = city_name_by_id.get(player_model.position_city_id)
            if city_name is None:
                raise ValueError(
                    f"Unknown city_id={player_model.position_city_id} for player '{player_model.name}' in game {code}"
                )
            
            city = game.cities.get_city_by_name(city_name)
            if city is None:
                raise ValueError(f"City '{city_name}' not found in CityGraph for game {code}")
            
            player = PlayerGame(
                game=game,
                player_id=player_model.id,
                name=player_model.name,
                role_id=player_model.role_id,
                pos=city
            )
            # Убеждаемся, что actions_left не отрицательный
            player.actions_left = max(0, player_model.actions_left) if player_model.actions_left is not None else 4
            game.players.append(player)
            
            player_by_id[player_model.id] = player

        # Load cards
        card_models = CardModel.query.all()
        card_model_by_id = {m.id: m for m in card_models}

        # Load deck of player cards
        deck_of_cards_rows = DeckOfCardsModel.query.filter_by(game_id=code).all()
    
        if deck_of_cards_rows:
            deck_of_cards_rows.sort(key=lambda x: (not x.in_game, x.order_index))

            deck_cards = DeckCards(game)
            
            for row in deck_of_cards_rows:
                card_model = card_model_by_id.get(row.card_id)
                if card_model is None:
                    raise ValueError(f"CardModel id={row.card_id} not found (game {code})")
                
                card_type = next(ct for ct in (CardType.CITY, CardType.EPIDEMIC, CardType.EVENT) if ct.name == card_model.type.name)
                
                card = CardGame(
                    card_id=card_model.id,
                    name=card_model.name,
                    card_type=card_type,
                    deck=deck_cards
                )
                
                if row.player_id is not None:
                    player = player_by_id[row.player_id]
                    if player is None:
                        raise ValueError(f"Unknown player_id={row.player_id} for card_id={row.card_id} (game {code})")
                    
                    card.player_owner = player

                if row.in_game:
                    deck_cards.draw_pile.append(card)
                else:
                    if row.player_id is not None:
                        raise ValueError(f"Discard pile card_id={row.card_id} has player_id={row.player_id} (invalid)")
                    deck_cards.discard_pile.append(card)
            
            game.deck_cards = deck_cards

        # Load deck of diseases cards
        deck_of_diseases_rows = DeckOfDiseasesModel.query.filter_by(game_id=code).all()
        
        if deck_of_diseases_rows:
            deck_of_diseases_rows.sort(key=lambda r: (not r.in_game, r.order_index))
            
            deck_diseases = DeckDiseases(game)

            for row in deck_of_diseases_rows:
                card_model = card_model_by_id.get(row.city_id)
                if card_model is None:
                    raise ValueError(f"CardModel id={row.city_id} not found (game {code})")

                card = CardGame(
                    card_id=card_model.id,
                    name=card_model.name,
                    card_type=CardType.CITY,
                    deck=deck_diseases
                )
                
                if row.in_game:
                    deck_diseases.draw_pile.append(card)
                else:
                    deck_diseases.discard_pile.append(card)


            game.deck_diseases = deck_diseases

        return game

    @staticmethod
    def delete_game(code: str) -> None:
        """
        Удаляет игру по коду.

        :param code: Код игры для удаления.
        """
        # Удаляем все данные, связанные с игрой
        db.session.query(GameSessionModel).filter_by(code=code).delete()
        db.session.query(GameStateModel).filter_by(game_id=code).delete()
        db.session.query(PlayerModel).filter_by(game_id=code).delete()
        db.session.query(CityStateModel).filter_by(game_id=code).delete()
        db.session.query(DeckOfCardsModel).filter_by(game_id=code).delete()
        db.session.query(DeckOfDiseasesModel).filter_by(game_id=code).delete()

        db.session.commit()

    @staticmethod
    def initialize_cities(game: PandemicGame) -> CityGraph:
        cities = CityGraph(game)
        cities_db = CityModel.query.all()

        for city in cities_db:
            color = next(c for c in ColorType if c.name == city.color.name)
            cities.add_city(city.id, city.name, color, city.population)

        city_connections = CityConnectionModel.query.all()
        for connection in city_connections:
            city_from = cities.get_city_by_id(connection.city_id)
            city_to = cities.get_city_by_id(connection.connected_city_id)
            if city_from and city_to:
                cities.connect(city_from.name, city_to.name)
        
        return cities

    @staticmethod
    def initialize_decks(game: PandemicGame) -> tuple[DeckCards, DeckDiseases]:
        deck_cards = DeckCards(game)
        deck_diseases = DeckDiseases(game)

        cities_db = CityModel.query.all()

        card_id = 0
        
        for city in cities_db:
            deck_cards.draw_pile.append(CardGame(card_id, city.name, CardType.CITY, deck_cards)) 
            deck_diseases.draw_pile.append(CardGame(card_id, city.name, CardType.CITY, deck_diseases)) 
            card_id += 1
            
        for _ in range(game.difficult.value):
            deck_cards.draw_pile.append(CardGame(card_id, CardType.EPIDEMIC.name, CardType.EPIDEMIC, deck_cards)) 
            card_id += 1
            
        deck_cards.shuffle()
        deck_diseases.shuffle()
        
        return deck_cards, deck_diseases
        