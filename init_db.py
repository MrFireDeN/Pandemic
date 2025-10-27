from sqlalchemy import inspect
from eng import db
from app import create_app

def create_db():
    app = create_app()
    with app.app_context():
        inspector = inspect(db.engine)
        db.create_all()
        print(inspector.get_table_names())

if __name__ == '__main__':
    create_db()