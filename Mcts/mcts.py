import math
import random
import copy

from mcts.node import Node
from auxiliares.helpers import get_valid_moves, apply_move, next_player
from game.logic import check_winner

MAX_SIMULATE_TURNS = 100


def uct(node, c=1.4):
    if node.visits == 0:
        return float("inf")

    return (node.wins / node.visits) + c * math.sqrt(
        math.log(node.parent.visits) / node.visits
    )


def select(node):
    while node.children:
        node = max(node.children, key=lambda n: uct(n))
    return node


def expand(node):

    moves = get_valid_moves(node.state, node.player)
    tried_moves = [child.move for child in node.children]

    for move in moves:
        if move not in tried_moves:

            new_state = copy.deepcopy(node.state)
            apply_move(new_state, move, node.player)

            child = Node(
                new_state,
                next_player(node.player),
                node,
                move
            )

            node.children.append(child)
            return child

    return node


def simulate(state, player):

    board = copy.deepcopy(state)
    current_player = player

    # BUG CORRIGIDO: limite de turnos para evitar loops infinitos em empate
    for _ in range(MAX_SIMULATE_TURNS):

        moves = get_valid_moves(board, current_player)

        if not moves:
            return None  # empate

        move = random.choice(moves)
        apply_move(board, move, current_player)

        if check_winner(board, current_player):
            return current_player

        current_player = next_player(current_player)

    return None  # empate por timeout


def backpropagate(node, winner, root_player):
    # BUG CORRIGIDO: cada nó regista vitórias do ponto de vista do seu próprio jogador,
    # não apenas do root_player. Assim o UCT reflecte corretamente quem beneficia de cada nó.
    while node:
        node.visits += 1

        if winner is not None and winner == node.player:
            node.wins += 1

        node = node.parent


def mcts(board, player, iterations=1000):

    root = Node(copy.deepcopy(board), player)

    for _ in range(iterations):

        node = select(root)
        node = expand(node)

        winner = simulate(node.state, node.player)

        backpropagate(node, winner, player)

    if not root.children:
        # fallback: sem filhos (sem jogadas válidas)
        return None

    best_child = max(root.children, key=lambda n: n.visits)

    return best_child.move