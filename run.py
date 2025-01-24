# run.py
from app import create_app
from app.extensions import socketio
import app.sockets

app = create_app()

if __name__ == "__main__":
    socketio.run(app, debug=True, use_reloader=True, log_output=True)
