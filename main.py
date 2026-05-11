from game.board import create_board, ROWS, COLS
from game.logic import check_winner, check_winner_after_pop, is_board_full, GameState
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


def check_game_over(board, move, player, game_state, mode):
    """
    Verifica todas as condições de fim de jogo após uma jogada:
      - Vitória normal ou por pop simultâneo (Regra 1)
      - Empate por tabuleiro cheio com opção de pop (Regra 2) — só para humanos
      - Empate por repetição (Regra 3)

    Devolve:
      ('win', winner)  — alguém ganhou
      ('draw', None)   — empate
      (None, None)     — jogo continua
    """
    move_type = move[0]
    opponent = next_player(player)

    # Regra 1: pop simultâneo
    if move_type == 'pop':
        winner = check_winner_after_pop(board, player)
        if winner:
            return ('win', winner)
    else:
        if check_winner(board, player):
            return ('win', player)

    # Regra 3: repetição de estado (qualquer jogador pode declarar empate)
    if game_state.is_threefold_repetition(board):
        print("Estado repetido 3 vezes!")
        if mode in ("1", "2"):
            # Em modo humano, perguntar se quer declarar empate
            choice = input("Queres declarar empate por repetição? (s/n): ").strip().lower()
            if choice == 's':
                return ('draw', None)
        else:
            # PC vs PC: declarar empate automaticamente
            return ('draw', None)

    # Regra 2: tabuleiro cheio
    if is_board_full(board):
        if mode in ("1", "2"):
            print("Tabuleiro cheio!")
            valid = get_valid_moves(board, player)
            pop_moves = [m for m in valid if m[0] == 'pop']
            if pop_moves:
                choice = input(f"{player}, queres fazer um pop ou declarar empate? (pop/empate): ").strip().lower()
                if choice == 'empate':
                    return ('draw', None)
                # Se escolher pop, o jogo continua — devolve None para o main tratar
                return ('board_full_pop', pop_moves)
            else:
                return ('draw', None)
        else:
            # PC vs PC com tabuleiro cheio: declarar empate
            return ('draw', None)

    return (None, None)


def main():
    print("Escolhe o modo de jogo:")
    print("1 - Jogador vs Jogador")
    print("2 - Jogador vs Computador (MCTS standard)")
    print("3 - Computador vs Computador (MCTS standard vs MCTS agressivo)")

    mode = input("Opção: ").strip()

    board = create_board()
    player = "X"
    game_state = GameState()

    while True:
        print_board(board)
        print(f"Turno: {player}")

        valid_moves = get_valid_moves(board, player)
        if not valid_moves:
            print(f"Sem jogadas válidas para {player}. Empate!")
            break

        # --- Escolha da jogada ---
        if mode == "1":
            move = get_human_move(board, player)

        elif mode == "2":
            if player == "X":
                move = get_human_move(board, player)
            else:
                move = mcts(board, player, iterations=1000)
                print(f"Computador (MCTS standard) joga: {move}")

        elif mode == "3":
            if player == "X":
                # MCTS explorador: c alto = explora mais ramos diferentes
                move = mcts(board, player, iterations=1000, c=1.4)
                print(f"Computador X (iterations=1000, c=1.4) joga: {move}")
            else:
                # MCTS focado: mais iterações + c baixo = aprofunda os melhores ramos
                move = mcts(board, player, iterations=2000, c=0.8)
                print(f"Computador O (iterations=2000, c=0.8) joga: {move}")

        else:
            print("Modo inválido.")
            return

        # --- Aplicar jogada ---
        apply_move(board, move, player)
        game_state.register(board)

        # --- Verificar fim de jogo ---
        result, data = check_game_over(board, move, player, game_state, mode)

        if result == 'win':
            print_board(board)
            print(f"{data} ganhou!")
            break

        elif result == 'draw':
            print_board(board)
            print("Empate!")
            break

        elif result == 'board_full_pop':
            # Humano escolheu fazer pop com tabuleiro cheio (Regra 2)
            pop_moves = data
            print("Jogadas pop disponíveis:", pop_moves)
            pop_move = get_human_move(board, player)
            apply_move(board, pop_move, player)
            game_state.register(board)
            # Verificar vitória após o pop extra
            winner = check_winner_after_pop(board, player)
            if winner:
                print_board(board)
                print(f"{winner} ganhou!")
                break

        # --- Próximo jogador ---
        player = next_player(player)


if __name__ == "__main__":
    main()