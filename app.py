from flask import Flask
app = Flask(__name__)

@app.route('/')
def game():
    return 'Pandemic!'

if __name__ == '__main__':
    app.run()
