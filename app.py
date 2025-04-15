from flask import Flask, render_template, request, redirect, url_for, make_response
from flask_socketio import SocketIO, join_room, emit
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import logging
import os
import eventlet

# Required for SocketIO (ensure async compatibility)
eventlet.monkey_patch()

# Flask app initialization
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'fallback_secret_key')
app.config['SESSION_COOKIE_SECURE'] = True  # Secure cookies for session
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Restrict session access to HTTP (protect against JS access)
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Prevent CSRF from cross-site requests

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Extensions
socketio = SocketIO(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Dummy user database (hashed passwords)
users = {
    os.getenv('TEST_USER', 'testuser'): {'password': os.getenv('TEST_USER_PASS', 'default_password')},
    os.getenv('TEST_USER2', 'testuser2'): {'password': os.getenv('TEST_USER2_PASS', 'default_password2')}
}




# User model
class User(UserMixin):
    def __init__(self, id):
        self.id = id


@login_manager.user_loader
def load_user(user_id):
    if user_id in users:
        return User(user_id)
    return None


# Routes
@app.route('/')
def home():
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Validate username and password
        if username in users and check_password_hash(users[username]['password'], password):
            login_user(User(username))
            return redirect(url_for('chat'))
        error = "Invalid credentials"

    return render_template('login.html', error=error)


@app.route('/chat')
@login_required
def chat():
    # Add headers to prevent caching of sensitive pages
    response = make_response(render_template('chat.html', username=current_user.id))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


# SocketIO Events
@socketio.on('join')
def on_join(data):
    try:
        username = data.get('username')
        room = data.get('room')

        # Validate input
        if not username or not room:
            emit('error', {'msg': 'Invalid input: username and room are required'})
            return

        join_room(room)
        emit('message', {'username': 'System', 'msg': f'{username} has joined the room.'}, room=room)
    except Exception as e:
        logging.error(f"Error in join event: {e}")
        emit('error', {'msg': 'An error occurred while processing your request', 'error': str(e)})


@socketio.on('send_message')
def handle_message(data):
    try:
        username = data.get('username', 'Unknown')
        msg = data.get('msg', '')
        room = data.get('room')

        # Validate input
        if not room:
            emit('error', {'msg': 'Invalid message: room is required'})
            return

        # Emit chat message to the room
        emit('message', {'username': username, 'msg': msg}, room=room)
    except Exception as e:
        logging.error(f"Error in send_message event: {e}")
        emit('error', {'msg': 'An error occurred while processing your message', 'error': str(e)})


# Main entry point
if __name__ == '__main__':
    debug_mode = os.getenv('FLASK_DEBUG', 'true').lower() == 'true'  # Control debug mode via env variables
    socketio.run(app, debug=debug_mode)

