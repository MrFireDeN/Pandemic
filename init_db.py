from sqlalchemy import inspect
from eng import db
from app import create_app

from models import CityModel, CardModel, CardTypeDB

def create_db():
    app = create_app()
    with app.app_context():
        inspector = inspect(db.engine)
        db.create_all()
        print(inspector.get_table_names())

def initialize_decks():
    app = create_app()
    with app.app_context():
        cities_db = CityModel.query.all()
    
        for city in cities_db:
            card_model = CardModel(
                name=city.name,
                description=f"City card for {city.name}",
                type=CardTypeDB.CITY,
                city_id=city.id,
            )
            db.session.add(card_model)
    
        card_model = CardModel(
            name=CardTypeDB.EPIDEMIC.name,
            description="Epidemic card",
            type=CardTypeDB.EPIDEMIC,
        )
        
        db.session.add(card_model)
        db.session.commit()

if __name__ == '__main__':
    # create_db()
    # initialize_decks()
    pass