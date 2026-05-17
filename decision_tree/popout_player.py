"""Ligacao entre a arvore de decisao e o jogo PopOut."""

import os

from auxiliares.helpers import get_valid_moves
from decision_tree.id3 import build_tree, predict
from popout_dataset import CELL_ATTRIBUTES, encode_board, label_to_move
from popout_tree_demo import load_popout_dataset


def train_popout_tree(dataset_path="popout_mcts_dataset.csv", max_depth=8):
    """Carrega o dataset PopOut e treina uma arvore para prever jogadas."""
    if not os.path.exists(dataset_path):
        raise FileNotFoundError(
            f"Dataset '{dataset_path}' nao encontrado. "
            "Gera primeiro com: python popout_dataset.py"
        )

    rows = load_popout_dataset(dataset_path)
    if not rows:
        raise ValueError("Dataset vazio. Gera novamente o dataset antes de treinar.")

    return build_tree(
        rows,
        CELL_ATTRIBUTES,
        target="move",
        max_depth=max_depth,
        split_mode="categorical",
    )


def choose_tree_move(board, player, tree):
    """Escolhe uma jogada usando a arvore treinada.

    Se a jogada prevista pela arvore nao for legal no estado atual, usa a
    primeira jogada valida como fallback.
    """
    valid_moves = get_valid_moves(board, player)
    if not valid_moves:
        return None

    # A arvore so entende linhas numericas, por isso o tabuleiro e codificado.
    encoded_state = encode_board(board, player)
    predicted_label = predict(tree, encoded_state)
    predicted_move = label_to_move(predicted_label)

    if predicted_move in valid_moves:
        return predicted_move

    return valid_moves[0]
