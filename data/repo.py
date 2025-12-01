from game import PandemicGame
from eng import db

from models import (CityModel, 
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
                    CityStateModel)

class GameRepository:
    def __init__(self):
        pass
        
    def save_game(self, game: PandemicGame) -> None:
        json_state = game.serialize()
        
        db.session.commit()
        
    def load_game(self, code: str) -> PandemicGame | None:
        return None
    
    def delete_game(self, code: str) -> None:
        db.session.query(GameSessionModel).filter_by(code=code).delete()
        db.session.commit()