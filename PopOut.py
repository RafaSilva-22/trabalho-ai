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

def is_valid_move(board, col):
    return board[0][col] == ' '

def drop_piece(board, col, player):
    for row in range(ROWS-1, -1, -1):
        if board[row][col] == ' ':
            board[row][col] = player
            return True
    return False

def pop_out(board, col, player):
    for row in range(ROWS):
        if board[row][col] == player:
            for r in range(row, ROWS-1):
                board[r][col] = board[r+1][col]
            board[ROWS-1][col] = ' '
            return True
    return False

def check_win(board, player):
    # Check horizontal
    for row in range(ROWS):
        for col in range(COLS - 3):
            if all(board[row][col+i] == player for i in range(4)):
                return True

    # Check vertical
    for col in range(COLS):
        for row in range(ROWS - 3):
            if all(board[row+i][col] == player for i in range(4)):
                return True

    # Check diagonal (bottom-left to top-right)
    for row in range(3, ROWS):
        for col in range(COLS - 3):
            if all(board[row-i][col+i] == player for i in range(4)):
                return True

    # Check diagonal (top-left to bottom-right)
    for row in range(ROWS - 3):
        for col in range(COLS - 3):
            if all(board[row+i][col+i] == player for i in range(4)):
                return True

    return False


def main():
    board = create_board()
    current_player = 'X'

    while True:
        print_board(board)
        move = input(f"Player {current_player}, enter column (0-{COLS-1}) to drop or 'p' followed by column to pop out: ")

        if move.startswith('p'):
            col = int(move[1:])
            if 0 <= col < COLS and pop_out(board, col, current_player):
                if check_win(board, current_player):
                    print_board(board)
                    print(f"Player {current_player} wins!")
                    break
                current_player = 'O' if current_player == 'X' else 'X'
            else:
                print("Invalid pop out move. Try again.")
        else:
            col = int(move)
            if 0 <= col < COLS and is_valid_move(board, col):
                drop_piece(board, col, current_player)
                if check_win(board, current_player):
                    print_board(board)
                    print(f"Player {current_player} wins!")
                    break
                current_player = 'O' if current_player == 'X' else 'X'
            else:
                print("Invalid move. Try again.")

if __name__ == "__main__":
    main()