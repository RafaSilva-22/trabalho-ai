from game.board import create_board, ROWS, COLS
from game.logic import check_winner
from mcts.mcts import mcts
from auxiliares.helpers import apply_move, next_player, get_valid_moves


def print_board(board):
    print()
    print("  " + " ".join(str(i) for i in range(COLS)))
    print("  " + "-" * (COLS * 2 - 1))
    for row in board:
        print("| " + " ".join(cell if cell != " " else "." for cell in row) + " |")
    print("  " + "-" * (COLS * 2 - 1))
    print()


def get_human_move(board, player):
    while True:
        move_type = input("Tipo (drop/pop): ").strip().lower()
        if move_type not in ("drop", "pop"):
            print("Tipo inválido. Usa 'drop' ou 'pop'.")
            continue
        try:
            col = int(input("Coluna (0-6): "))
        except ValueError:
            print("Coluna inválida.")
            continue
        move = (move_type, col)
        if move in get_valid_moves(board, player):
            return move
        else:
            print("Jogada inválida. Tenta outra.")


def main():

    print("Escolhe o modo de jogo:")
    print("1 - Jogador vs Jogador")
    print("2 - Jogador vs Computador")
    print("3 - Computador vs Computador")

    mode = input("Opção: ")

    board = create_board()
    player = "X"

    while True:

        print_board(board)
        print(f"Turno: {player}")

        valid_moves = get_valid_moves(board, player)
        if not valid_moves:
            print(f"Sem jogadas válidas para {player}. Empate!")
            break

        if mode == "1":
            move = get_human_move(board, player)
            apply_move(board, move, player)

        elif mode == "2":
            if player == "X":
                move = get_human_move(board, player)
            else:
                move = mcts(board, player, iterations=1000)
                print("Computador joga:", move)
            apply_move(board, move, player)

        elif mode == "3":
            move = mcts(board, player, iterations=1000)
            print("Computador joga:", move)
            apply_move(board, move, player)

        else:
            print("Modo inválido")
            return

        if check_winner(board, player):
            print_board(board)
            print(f"{player} ganhou!")
            break

        player = next_player(player)


if __name__ == "__main__":
    main()