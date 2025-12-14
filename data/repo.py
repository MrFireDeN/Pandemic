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
        serialized_game = game.serialize()

        game_session = GameSessionModel(
            code=game.code,
            status=game.phase,
        )
        existing_session = GameSessionModel.query.filter_by(code=game.code).first()
        if existing_session:
            # Если сессия существует, обновляем её
            existing_session.status = game.phase
            db.session.merge(existing_session)  # Используем merge для обновления
        else:
            # Если сессии нет, добавляем новую
            db.session.add(game_session)
    
        # Save the board state (сохраняем данные доски)
        board_data = game.board.serialize()
        
        if isinstance(board_data, str):
            board_data = json.loads(board_data)

        board_model = GameStateModel.query.filter_by(game_id=game.code).first()
        if board_model:
            board_model.turn_order = board_data["turn_order"]
            board_model.outbreak_indicator = board_data["outbreak_indicator"]
            board_model.infection_indicator = board_data["infection_indicator"]
            board_model.cubes_per_color = json.dumps(board_data["cubes_per_color"])
            board_model.vaccines_state = json.dumps(board_data["vaccines_state"])
        else:
            board_model = GameStateModel(
                game_id=game.code,
                turn_order=board_data["turn_order"],
                outbreak_indicator=board_data["outbreak_indicator"],
                infection_indicator=board_data["infection_indicator"],
                cubes_per_color=json.dumps(board_data["cubes_per_color"]),
                vaccines_state=json.dumps(board_data["vaccines_state"]),
            )
            db.session.add(board_model)
    
        # Save the cities
        for city_name, city in game.cities.cities_by_name.items():
            city_state_model = CityStateModel(
                id=city.id,
                game_id=game.code,
                city_id=city.id,
                has_station=city.has_station,
                red=city.infection_cubes[ColorType.red],
                yellow=city.infection_cubes[ColorType.yellow],
                blue=city.infection_cubes[ColorType.blue],
                black=city.infection_cubes[ColorType.black],
            )
            db.session.merge(city_state_model)
    
        # Save the players
        for player in game.players:
            player_data = player.serialize()
            player_model = PlayerModel(
                id=player_data["id"],
                name=player_data["name"],
                game_id=game.code,
                role_id=player_data["role"],
                position_city_id=player_data["position_city"],
                actions_left=player_data["actions_left"],
            )
            db.session.merge(player_model)
            
        if game.deck_cards:
            for order_index, card in enumerate(game.deck_cards.draw_pile):
                card_data = card.serialize()
        
                if isinstance(card_data, str):
                    card_data = json.loads(card_data)
        
                deck_card_model = DeckOfCardsModel.query.filter_by(game_id=game.code, card_id=card_data["id"]).first()
        
                if deck_card_model:
                    deck_card_model.order_index = order_index
                    deck_card_model.in_game = True
                    deck_card_model.player_id = card_data["player_owner"]
                else:
                    deck_card_model = DeckOfCardsModel(
                        card_id=card_data["id"],
                        game_id=game.code,
                        player_id=card_data["player_owner"],
                        order_index=order_index,
                        in_game=True,
                    )
                    db.session.add(deck_card_model)
        
            for order_index, card in enumerate(game.deck_cards.discard_pile):
                card_data = card.serialize()
        
                deck_card_model = DeckOfCardsModel.query.filter_by(game_id=game.code, card_id=card_data["id"]).first()
        
                if deck_card_model:
                    deck_card_model.order_index = order_index
                    deck_card_model.in_game = False
                    deck_card_model.player_id = card_data["player_owner"]
                else:
                    deck_card_model = DeckOfCardsModel(
                        card_id=card_data["id"],
                        game_id=game.code,
                        player_id=card_data["player_owner"],
                        order_index=order_index,
                        in_game=False,
                    )
                    db.session.add(deck_card_model)
        
        if game.deck_diseases:
            for order_index, city in enumerate(game.deck_diseases.draw_pile):
                deck_disease_model = DeckOfDiseasesModel.query.filter_by(game_id=game.code, city_id=city.id).first()
        
                if deck_disease_model:
                    deck_disease_model.order_index = order_index
                    deck_disease_model.in_game = True
                else:
                    deck_disease_model = DeckOfDiseasesModel(
                        city_id=city.id,
                        game_id=game.code,
                        order_index=order_index,
                        in_game=True,
                    )
                    db.session.add(deck_disease_model)
        
            for order_index, city in enumerate(game.deck_diseases.discard_pile):
                deck_disease_model = DeckOfDiseasesModel.query.filter_by(game_id=game.code, city_id=city.id).first()
        
                if deck_disease_model:
                    deck_disease_model.order_index = order_index
                    deck_disease_model.in_game = False
                else:
                    deck_disease_model = DeckOfDiseasesModel(
                        city_id=city.id,
                        game_id=game.code,
                        order_index=order_index,
                        in_game=False,
                    )
                    db.session.add(deck_disease_model)
    
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
        game.status = session.status

        # Load the board state
        board_data = GameStateModel.query.filter_by(game_id=code).first()
        if board_data:
            game.board.deserialize(game, {
                "turn_order": board_data.turn_order,
                "outbreak_indicator": board_data.outbreak_indicator,
                "infection_indicator": board_data.infection_indicator,
                "cubes_per_color": json.loads(board_data.cubes_per_color),
                "vaccines_state": json.loads(board_data.vaccines_state),
            })
        else:
            print(f"Board data for game {code} not found.")

        city_state_data = CityStateModel.query.filter_by(game_id=code).all()
        for city_state in city_state_data:
            city = game.cities.get_city_by_id(city_state.city_id)
            if city:
                city.has_station = city_state.has_station
                city.infection_cubes[ColorType.red] = city_state.red
                city.infection_cubes[ColorType.yellow] = city_state.yellow
                city.infection_cubes[ColorType.blue] = city_state.blue
                city.infection_cubes[ColorType.black] = city_state.black

        # Load the players
        players = PlayerModel.query.filter_by(game_id=code).all()
        for player_model in players:
            player_data = {
                "id": player_model.id,
                "name": player_model.name,
                "role": player_model.role_id,
                "pos": player_model.position_city_id,
                "actions_left": player_model.actions_left,
            }
            player = PlayerGame.deserialize(player_data, game)
            game.players.append(player)

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
            cities.add_city(city.id, city.name, color)

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
        