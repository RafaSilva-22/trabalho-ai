from game.board import drop_piece, pop_piece

def next_player(player):
    return "O" if player == "X" else "X"


def apply_move(board, move, player):
    move_type, col = move

    if move_type == "drop":
        drop_piece(board, col, player)
    else:
        pop_piece(board, col, player)


def get_valid_moves(board, player):

    moves = []

    for col in range(7):
        if board[0][col] == " ":
            moves.append(("drop", col))

    for col in range(7):
        if board[5][col] == player:
            moves.append(("pop", col))

    return moves