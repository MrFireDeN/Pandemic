from flask import Flask, render_template
from eng import db, socketio
from controller import load_game_sessions
from models import PlayerModel

def create_app():
    app = Flask(__name__, template_folder='templates')
    app.config.from_object("config.Config")

    db.init_app(app)
    socketio.init_app(app)

    load_game_sessions(app)

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/host/<code>")
    def host_room(code):
        return render_template("host.html", code=code)

    @app.route("/join")
    def join():
        return render_template("join.html")

    @app.route("/board/<code>")
    def board(code):
        return render_template("board.html", code=code)
    
    @app.route("/player/<code>/<name>")
    def player(code, name):
        player = PlayerModel.query.filter_by(game_id=code, name=name).first()
        return render_template("player.html", code=code, name=name, player_id=player.id if player else "")


    from controller import api
    app.register_blueprint(api, url_prefix="/api")

    return app

if __name__ == '__main__':
    app = create_app()
    socketio.run(app, debug=True, host="0.0.0.0", port=5000, allow_unsafe_werkzeug=True)
