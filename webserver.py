from flask import Flask
from threading import Thread

app = Flask(__name__)

@app.route('/')
def home():
    return "Expertise is  currently  running"

def run():
    app.run(host="0.0.0.0", port=6923)

def keep_alive():
    t = Thread(target=run)
    t.start()

if __name__ == "__main__":
    keep_alive()
