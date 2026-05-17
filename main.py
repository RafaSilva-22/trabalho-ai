from game.board import create_board, ROWS, COLS
from game.logic import check_winner, check_winner_after_pop, is_board_full, GameState
from Mcts.mcts import mcts
from Mcts.mctsAlternativo import mcts_epsilon_greedy
from auxiliares.helpers import apply_move, next_player, get_valid_moves
from decision_tree.popout_player import choose_tree_move, train_popout_tree


def print_board(board):
    print()
    print("  " + " ".join(str(i) for i in range(COLS)))
    print("  " + "-" * (COLS * 2 - 1))
    for row in board:
        print("| " + " ".join(cell if cell != " " else "." for cell in row) + " |")
    print("  " + "-" * (COLS * 2 - 1))
    print()


def get_human_move(board, player, allowed_moves=None):
    valid_moves = allowed_moves if allowed_moves is not None else get_valid_moves(board, player)

    while True:
        move_type = input("Tipo (drop/pop): ").strip().lower()
        if move_type not in ("drop", "pop"):
            print("Tipo invalido. Usa 'drop' ou 'pop'.")
            continue
        try:
            col = int(input("Coluna (0-6): "))
        except ValueError:
            print("Coluna invalida.")
            continue
        move = (move_type, col)
        if move in valid_moves:
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
    human_turn = mode == "1" or (mode in ("2", "4") and player == "X")

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
        if human_turn:
            # Em modo humano, perguntar se quer declarar empate
            choice = input("Queres declarar empate por repeticao? (s/n): ").strip().lower()
            if choice == 's':
                return ('draw', None)
        else:
            # PC vs PC: declarar empate automaticamente
            return ('draw', None)

    # Regra 2: tabuleiro cheio
    if is_board_full(board):
        if human_turn:
            print("Tabuleiro cheio!")
            valid = get_valid_moves(board, player)
            pop_moves = [m for m in valid if m[0] == 'pop']
            if pop_moves:
                choice = input(f"{player}, queres fazer um pop ou declarar empate? (pop/empate): ").strip().lower()
                if choice == 'empate':
                    return ('draw', None)
                # Se escolher pop, o jogo continua - devolve None para o main tratar
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
    print("4 - Jogador vs Computador (Arvore ID3)")
    print("5 - Computador vs Computador (MCTS vs Arvore ID3)")

    mode = input("Opcao: ").strip()

    tree = None
    if mode in ("4", "5"):
        try:
            print("A treinar arvore ID3 com popout_mcts_dataset.csv...")
            tree = train_popout_tree("popout_mcts_dataset.csv", max_depth=8)
            print("Arvore ID3 pronta.")
        except (FileNotFoundError, ValueError) as error:
            print(error)
            return

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
                move = mcts(board, player, iterations=2000, c=1.4)
                print(f"Computador X - MCTS UCT (iterations=2000, c=1.4) joga: {move}")
            else:
                move = mcts_epsilon_greedy(board, player, iterations=2000, epsilon=0.2)
                print(f"Computador O - MCTS ε-greedy (iterations=2000, epsilon=0.2) joga: {move}")

        elif mode == "4":
            if player == "X":
                move = get_human_move(board, player)
            else:
                move = choose_tree_move(board, player, tree)
                print(f"Computador (Arvore ID3) joga: {move}")

        elif mode == "5":
            if player == "X":
                move = mcts(board, player, iterations=1000, c=1.4)
                print(f"Computador X - MCTS UCT joga: {move}")
            else:
                move = choose_tree_move(board, player, tree)
                print(f"Computador O - Arvore ID3 joga: {move}")

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