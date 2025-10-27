from flask import Flask, render_template
from config import Config
from eng import db, socketio

def create_app():
    app = Flask(__name__, template_folder='templates')
    app.config.from_object("config.Config")

    db.init_app(app)
    socketio.init_app(app)

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/host/<code>")
    def host_room(code):
        return render_template("host.html", code=code)

    @app.route("/join")
    def join():
        return render_template("join.html")


    from controller import api
    app.register_blueprint(api, url_prefix="/api")

    return app

if __name__ == '__main__':
    app = create_app()
    socketio.run(app, debug=True, host="0.0.0.0", port=5000, allow_unsafe_werkzeug=True)
