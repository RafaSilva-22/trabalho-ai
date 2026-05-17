"""Geracao do dataset PopOut usando jogadas escolhidas pelo MCTS.

Cada exemplo do CSV representa:
- o estado atual do tabuleiro codificado em 42 variaveis cell_linha_coluna;
- a jogada recomendada pelo MCTS na coluna/acao "move".
"""

import argparse
import csv
import random
import time

from auxiliares.helpers import apply_move, get_valid_moves, next_player
from game.board import COLS, ROWS, create_board
from game.logic import check_winner, check_winner_after_pop
from Mcts.mcts import mcts


CELL_ATTRIBUTES = [
    f"cell_{row}_{col}"
    for row in range(ROWS)
    for col in range(COLS)
]


def move_to_label(move):
    """Converte uma jogada em texto para guardar no CSV."""
    move_type, col = move
    return f"{move_type}_{col}"


def label_to_move(label):
    """Converte uma label do CSV de volta para a jogada original."""
    move_type, col = label.split("_")
    return move_type, int(col)


def move_wins(board, move, player):
    """Verifica se a jogada acabou o jogo segundo as regras do PopOut."""
    if move[0] == "pop":
        return check_winner_after_pop(board, player) == player
    return check_winner(board, player)


def encode_cell(value, player):
    """Codifica uma casa do tabuleiro do ponto de vista do jogador atual."""
    if value == " ":
        return 0
    if value == player:
        return 1
    return -1


def encode_board(board, player):
    """Transforma o tabuleiro inteiro num dicionario de atributos numericos."""
    row = {}
    for r in range(ROWS):
        for c in range(COLS):
            row[f"cell_{r}_{c}"] = encode_cell(board[r][c], player)
    return row


def randomize_opening(board, player, max_random_moves):
    """Faz algumas jogadas aleatorias iniciais para variar os estados."""
    moves_to_play = random.randint(0, max_random_moves)
    current = player

    for _ in range(moves_to_play):
        moves = get_valid_moves(board, current)
        if not moves:
            break

        move = random.choice(moves)
        apply_move(board, move, current)

        if move_wins(board, move, current):
            return next_player(current), True

        current = next_player(current)

    return current, False


def generate_examples(
    games=80,
    iterations=50,
    max_turns=25,
    max_random_opening=8,
    max_examples=1000,
):
    """Gera exemplos jogando partidas em que o MCTS escolhe as jogadas."""
    examples = []

    for _ in range(games):
        if max_examples is not None and len(examples) >= max_examples:
            break

        board = create_board()
        player, finished = randomize_opening(board, "X", max_random_opening)
        if finished:
            continue

        for _ in range(max_turns):
            if max_examples is not None and len(examples) >= max_examples:
                break

            valid_moves = get_valid_moves(board, player)
            if not valid_moves:
                break

            move = mcts(board, player, iterations=iterations)
            if move is None or move not in valid_moves:
                break

            # Guarda o estado antes da jogada e a jogada escolhida como classe.
            example = encode_board(board, player)
            example["move"] = move_to_label(move)
            examples.append(example)

            apply_move(board, move, player)
            if move_wins(board, move, player):
                break

            player = next_player(player)

    return examples


def save_dataset(examples, path):
    """Guarda os exemplos num ficheiro CSV."""
    fieldnames = CELL_ATTRIBUTES + ["move"]

    with open(path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(examples)


def main():
    """Ponto de entrada para gerar o dataset pela linha de comandos."""
    parser = argparse.ArgumentParser(
        description="Gera um dataset PopOut com estados e jogadas sugeridas pelo MCTS."
    )
    parser.add_argument("--output", default="popout_mcts_dataset.csv")
    parser.add_argument("--games", type=int, default=80)
    parser.add_argument("--iterations", type=int, default=25)
    parser.add_argument("--max-turns", type=int, default=25)
    parser.add_argument("--max-random-opening", type=int, default=8)
    parser.add_argument("--max-examples", type=int, default=1000)
    parser.add_argument("--seed", type=int)
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    start_time = time.perf_counter()
    examples = generate_examples(
        games=args.games,
        iterations=args.iterations,
        max_turns=args.max_turns,
        max_random_opening=args.max_random_opening,
        max_examples=args.max_examples,
    )
    save_dataset(examples, args.output)
    elapsed_time = time.perf_counter() - start_time

    print(f"Dataset guardado em {args.output}")
    print(f"Exemplos gerados: {len(examples)}")
    print(f"Tempo de geracao: {elapsed_time:.2f} segundos")


if __name__ == "__main__":
    main()
