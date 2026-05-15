"""Exemplo simples de treino da arvore ID3 com o dataset Iris.

Este ficheiro serve como demonstracao isolada da arvore de decisao antes de a
usar no PopOut.
"""

import csv
import random

from decision_tree.id3 import accuracy, build_tree, predict, print_tree


ATTRIBUTES = ["sepallength", "sepalwidth", "petallength", "petalwidth"]
TARGET = "class"


def load_iris(path="iris.csv"):
    """Carrega o CSV Iris e converte os atributos numericos para float."""
    rows = []
    with open(path, newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            rows.append({
                attribute: float(row[attribute])
                for attribute in ATTRIBUTES
            } | {TARGET: row[TARGET]})
    return rows


def train_test_split(rows, test_ratio=0.2, seed=7):
    """Divide o dataset em treino e teste de forma reprodutivel."""
    shuffled = rows[:]
    random.Random(seed).shuffle(shuffled)
    split = int(len(shuffled) * (1 - test_ratio))
    return shuffled[:split], shuffled[split:]


def main():
    """Treina a arvore no Iris e imprime a arvore e as metricas."""
    rows = load_iris()
    train_rows, test_rows = train_test_split(rows)

    tree = build_tree(train_rows, ATTRIBUTES, TARGET)

    print("Arvore aprendida com ID3:")
    print_tree(tree)

    print()
    print(f"Exemplos de treino: {len(train_rows)}")
    print(f"Exemplos de teste: {len(test_rows)}")
    print(f"Accuracy treino: {accuracy(tree, train_rows, TARGET):.2%}")
    print(f"Accuracy teste: {accuracy(tree, test_rows, TARGET):.2%}")

    print()
    print("Primeiras previsoes no conjunto de teste:")
    for row in test_rows[:5]:
        expected = row[TARGET]
        predicted = predict(tree, row)
        print(f"esperado={expected:15s} previsto={predicted}")


if __name__ == "__main__":
    main()
