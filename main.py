from game.board import create_board, ROWS, COLS, print_board, is_valid_move, drop_piece, pop_out, check_win
from game.logic import is_valid_move, check_win



def main():

    print("Choose a game mode:")
    print("1. Player vs Player")
    print("2. Player vs Computer")
    print("3. Computer vs Computer")
    mode = input("Enter choice (1, 2, or 3): ")


    if mode == '1':
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
    else:
        print("This game mode is not implemented yet. Please choose Player vs Player (1).")

if __name__ == "__main__":
    main()