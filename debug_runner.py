from app import create_app
from data.enums import ColorType, CardType
from data.players import PlayerGame
from game import PandemicGame
from models import GameSessionModel
from data.repo import GameRepository

def main() -> None:
    app = create_app()  # db.init_app + load_game_sessions внутри :contentReference[oaicite:3]{index=3}

    with app.app_context():
        gs = GameSessionModel.query.first()
        if gs is None:
            raise RuntimeError("В БД нет ни одной GameSessionModel. Создайте хост-сессию через /host/create.")

        game = GameRepository.load_game(gs.code)  # грузим полное состояние игры из БД
        
        def test_start_game():
            print(game.start_game())
            
        def test_move_player():
            card_to_use = None
            for card in game.deck_cards.draw_pile:
                if card.player_owner is not None:
                    card_to_use = card
                    break
                    
            to_city_name = card_to_use.name

            print(to_city_name)

            player1_name = game.players[0].name

            print(player1_name)
            
            print(game.move_player(player1_name, to_city_name, card_to_use))
            
        def test_cure_city(city_name: str) -> None:
            card_to_use = None
        
            player1_name = game.players[0].name

            print(player1_name)

            color = game.cities.get_city_by_name(city_name).color

            print(color)
    
            print(game.cure_city_player(player1_name, city_name, color))
            
        def test_turn_end():
            print(game.notify_turn_ended())
            
        def test_trade_card_player():
            player1_name = game.players[0].name
            player2_name = game.players[1].name
            
            card_to_trade = None
            for card in game.deck_cards.draw_pile:
                if card.player_owner is None:
                    continue
                
                if card.player_owner.name is player1_name:
                    card_to_trade = card
                    break
            
            print(game.trade_card_player(player1_name, player2_name, card_to_trade))
            
        def test_discover_cure_player():
            player2_name = game.players[1].name
            print(player2_name)
            
            cards_to_discover = []
            for card in game.deck_cards.draw_pile:
                if card.player_owner is None:
                    continue
                    
                if len(cards_to_discover) == 5:
                    break
                    
                if card.player_owner.name is player2_name:
                    cards_to_discover.append(card)
                    
            color = ColorType.blue
            print(color)
            
            print(game.discover_cure_player(player2_name, color, cards_to_discover))
            
        print(game.difficult.value)

        # test_start_game()
        # test_move_player()
        # test_turn_end()
        # test_cure_city()
        # test_trade_card_player()
        # test_discover_cure_player()

        test_trade_card_player()

        print(f"Loaded game: code={game.code}, phase={game.phase}, players={len(game.players)}")
        
        

if __name__ == "__main__":
    main()
