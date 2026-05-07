import math
import random
import copy

from mcts.node import Node
from auxiliares.helpers import get_valid_moves, apply_move, next_player
from game.logic import check_winner
from mcts.heuristica import evaluate_board, is_bad_pop

MAX_SIMULATE_TURNS = 100
COLUMN_PRIORITY = [3, 2, 4, 1, 5, 0, 6]


def uct(node, c=1.4):
    if node.visits == 0:
        return float("inf")
    return (node.wins / node.visits) + c * math.sqrt(
        math.log(node.parent.visits) / node.visits
    )


def select(node):
    while node.children:
        moves = get_valid_moves(node.state, node.player)
        tried = [ch.move for ch in node.children]
        if len(tried) < len(moves):
            return node
        node = max(node.children, key=lambda n: uct(n))
    return node


def check_immediate_win(board, move, player):
    test = copy.deepcopy(board)
    apply_move(test, move, player)
    return check_winner(test, player)


def order_moves(moves, board, player):
    """
    Ordena e filtra movimentos por qualidade:
    1. Vitória imediata
    2. Bloqueio de vitória adversária
    3. Drops que prolongam sequências (2+ em linha)
    4. Drops centrais
    5. Pops razoáveis
    6. Pops maus (descartados)
    """
    opponent = next_player(player)
    wins, blocks, good_drops, neutral_drops, pops = [], [], [], [], []

    for move in moves:
        move_type, col = move

        # Descartar pops prejudiciais
        if move_type == 'pop' and is_bad_pop(board, col, player):
            continue

        if check_immediate_win(board, move, player):
            wins.append(move)
        elif check_immediate_win(board, move, opponent):
            blocks.append(move)
        elif move_type == 'drop':
            # Verificar se o drop cria/prolonga uma sequência
            test = copy.deepcopy(board)
            apply_move(test, move, player)
            score = evaluate_board(test, player)
            if score >= 10:  # contribui para sequência
                good_drops.append((score, move))
            else:
                neutral_drops.append(move)
        else:
            pops.append(move)

    good_drops.sort(key=lambda x: -x[0])
    good_sorted = [m for _, m in good_drops]

    # Ordenar neutral_drops por prioridade de coluna
    neutral_drops.sort(key=lambda m: COLUMN_PRIORITY.index(m[1]) if m[1] < 7 else 99)

    return wins + blocks + good_sorted + neutral_drops + pops


def expand(node):
    moves = get_valid_moves(node.state, node.player)
    tried_moves = [ch.move for ch in node.children]
    ordered = order_moves(moves, node.state, node.player)

    for move in ordered:
        if move not in tried_moves:
            new_state = copy.deepcopy(node.state)
            apply_move(new_state, move, node.player)
            child = Node(new_state, next_player(node.player), node, move)
            node.children.append(child)
            return child

    return node  # todos expandidos


def simulate(state, player):
    """
    Rollout heurístico:
    1. Ganhar imediatamente
    2. Bloquear vitória adversária
    3. Escolher o melhor move por avaliação de tabuleiro (com ruído)
    4. Evitar pops maus
    """
    board = copy.deepcopy(state)
    current = player

    for _ in range(MAX_SIMULATE_TURNS):
        moves = get_valid_moves(board, current)
        if not moves:
            return None

        opponent = next_player(current)

        # 1. Vitória imediata
        win = next((m for m in moves if check_immediate_win(board, m, current)), None)
        if win:
            apply_move(board, win, current)
            return current

        # 2. Bloquear
        block = next((m for m in moves if check_immediate_win(board, m, opponent)), None)

        if block:
            chosen = block
        else:
            # 3. Filtrar pops maus e avaliar os restantes com ruído
            candidates = [m for m in moves
                          if not (m[0] == 'pop' and is_bad_pop(board, m[1], current))]
            if not candidates:
                candidates = moves  # fallback se todos os pops são maus

            scored = []
            for m in candidates:
                test = copy.deepcopy(board)
                apply_move(test, m, current)
                s = evaluate_board(test, current)
                # Ruído: evita que o rollout seja completamente determinístico
                s += random.uniform(-5, 5)
                scored.append((s, m))

            scored.sort(key=lambda x: -x[0])
            # Escolher entre os top 3 para manter diversidade
            top = scored[:3]
            chosen = random.choice(top)[1]

        apply_move(board, chosen, current)
        if check_winner(board, current):
            return current
        current = next_player(current)

    return None


def backpropagate(node, winner, root_player):
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
        moves = get_valid_moves(board, player)
        # Fallback com heurística
        if moves:
            ordered = order_moves(moves, board, player)
            return ordered[0] if ordered else moves[0]
        return None

    best = max(root.children, key=lambda n: n.visits)
    return best.move