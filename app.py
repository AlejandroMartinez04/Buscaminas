from flask import Flask, render_template
from flask_socketio import SocketIO, emit, join_room, leave_room
import random
import uuid

app = Flask(__name__)
socketio = SocketIO(app)

# Diccionario para almacenar el estado de cada juego
games = {}

def create_board(rows, cols, mines_count):
    # Asegurarse de que la cantidad de minas no exceda el número total de celdas
    if mines_count > rows * cols:
        mines_count = rows * cols

    board = [[0 for _ in range(cols)] for _ in range(rows)]
    mines = random.sample(range(rows * cols), mines_count)
    
    for mine in mines:
        row = mine // cols
        col = mine % cols
        board[row][col] = -1  # -1 representa una mina
        
        # Incrementar el contador de minas en las celdas adyacentes
        for r in range(max(0, row - 1), min(rows - 1, row + 1) + 1):
            for c in range(max(0, col - 1), min(cols - 1, col + 1) + 1):
                if board[r][c] != -1:
                    board[r][c] += 1
                    
    return board, mines  # Devolver también las minas

@socketio.on('start_game')
def start_game(data):
    game_id = str(uuid.uuid4())  # Generar un ID único para el juego
    rows = int(data['rows'])
    cols = int(data['cols'])
    mines_count = int(data['mines'])
    
    # Crear el tablero y almacenar el estado del juego
    board, mines = create_board(rows, cols, mines_count)  # Obtener también las minas
    games[game_id] = {'board': board, 'mines': mines}  # Almacenar las minas en el estado del juego
    
    # Unir al cliente a la sala del juego
    join_room(game_id)
    
    emit('game_started', {'board': board, 'game_id': game_id}, room=game_id)

@socketio.on('cell_clicked')
def cell_clicked(data):
    game_id = data['game_id']
    row = data['row']
    col = data['col']
    
    board = games[game_id]['board']
    
    if board[row][col] == -1:
        emit('cell_result', {'row': row, 'col': col, 'value': -1}, room=game_id)
    else:
        emit('cell_result', {'row': row, 'col': col, 'value': board[row][col]}, room=game_id)

@socketio.on('reveal_mines')
def reveal_mines(data):
    game_id = data['game_id']
    mines = games[game_id]['mines']
    emit('mines_revealed', {'mines': mines}, room=game_id)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    socketio.run(app)