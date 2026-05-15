"""Treino e avaliacao da arvore ID3 no dataset PopOut.

Este ficheiro nao gera o dataset. Ele carrega o CSV ja criado por
popout_dataset.py, treina a arvore e mostra metricas de desempenho.
"""

import argparse
import csv
import random
from collections import Counter

from auxiliares.helpers import get_valid_moves
from decision_tree.id3 import accuracy, build_tree, predict, print_tree
from popout_dataset import CELL_ATTRIBUTES, label_to_move


def load_popout_dataset(path):
    """Carrega o CSV PopOut e converte as celulas para inteiros."""
    rows = []
    with open(path, newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            converted = {
                attribute: int(row[attribute])
                for attribute in CELL_ATTRIBUTES
            }
            converted["move"] = row["move"]
            rows.append(converted)
    return rows


def train_test_split(rows, test_ratio=0.2, seed=11):
    """Divide os exemplos em treino e teste de forma reprodutivel."""
    shuffled = rows[:]
    random.Random(seed).shuffle(shuffled)
    split = int(len(shuffled) * (1 - test_ratio))
    return shuffled[:split], shuffled[split:]


def row_to_board(row):
    """Reconstroi um tabuleiro simples a partir de uma linha codificada."""
    board = [[" " for _ in range(7)] for _ in range(6)]
    for r in range(6):
        for c in range(7):
            value = row[f"cell_{r}_{c}"]
            if value == 1:
                board[r][c] = "X"
            elif value == -1:
                board[r][c] = "O"
    return board


def legal_move_accuracy(tree, rows):
    """Mede quantas previsoes da arvore correspondem a jogadas legais."""
    if not rows:
        return 0.0

    legal = 0
    for row in rows:
        predicted = label_to_move(predict(tree, row))
        board = row_to_board(row)
        if predicted in get_valid_moves(board, "X"):
            legal += 1

    return legal / len(rows)


def main():
    """Treina a arvore no dataset PopOut e imprime resultados."""
    parser = argparse.ArgumentParser(
        description="Treina uma arvore ID3 para imitar jogadas MCTS no PopOut."
    )
    parser.add_argument("--dataset", default="popout_mcts_dataset.csv")
    parser.add_argument("--max-depth", type=int, default=15)
    parser.add_argument("--show-tree", action="store_true")
    args = parser.parse_args()

    rows = load_popout_dataset(args.dataset)
    if not rows:
        print("Dataset vazio. Gera primeiro com: python popout_dataset.py")
        return

    print(f"Dataset carregado de {args.dataset}")
    print(f"Exemplos carregados: {len(rows)}")

    train_rows, test_rows = train_test_split(rows)
    tree = build_tree(
        train_rows,
        CELL_ATTRIBUTES,
        target="move",
        max_depth=args.max_depth,
        split_mode="categorical",
    )

    print("Classes mais frequentes no dataset:")
    for move, count in Counter(row["move"] for row in rows).most_common(10):
        print(f"{move}: {count}")

    if args.show_tree:
        print()
        print("Arvore aprendida com ID3:")
        print_tree(tree)

    print()
    print(f"Exemplos totais: {len(rows)}")
    print(f"Exemplos de treino: {len(train_rows)}")
    print(f"Exemplos de teste: {len(test_rows)}")
    print(f"Accuracy treino: {accuracy(tree, train_rows, 'move'):.2%}")
    print(f"Accuracy teste: {accuracy(tree, test_rows, 'move'):.2%}")
    print(f"Jogadas legais no teste: {legal_move_accuracy(tree, test_rows):.2%}")

    print()
    print("Primeiras previsoes no conjunto de teste:")
    for row in test_rows[:8]:
        expected = row["move"]
        predicted = predict(tree, row)
        print(f"esperado={expected:8s} previsto={predicted}")


if __name__ == "__main__":
    main()
