ROWS = 6
COLS = 7




def create_board():
    board = []
    for _ in range(ROWS):
        board.append([' ' for _ in range(COLS)])
    return board

def print_board(board):
    for row in board:
        print('| ' + ' | '.join(row) + ' |')
    print('  ' + '   '.join(str(i) for i in range(COLS)))

def drop_piece(board, col, player):
    for row in range(ROWS-1, -1, -1):
        if board[row][col] == ' ':
            board[row][col] = player
            return True
    return False

def pop_piece(board, col, player):

    if board[ROWS - 1][col] != player:
        return False

    for r in range(ROWS - 1, 0, -1):
        board[r][col] = board[r - 1][col]

    board[0][col] = " "

    return True
