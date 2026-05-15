import math
import random
import copy

from mcts.node import Node
from auxiliares.helpers import get_valid_moves, apply_move, next_player
from game.logic import check_winner, check_winner_after_pop
from mcts.heuristica import evaluate_board, is_bad_pop

MAX_SIMULATE_TURNS = 100
COLUMN_PRIORITY = [3, 2, 4, 1, 5, 0, 6]


# ---------------------------------------------------------------------------
# MCTS com política ε-greedy
#
# Diferença fundamental face ao MCTS standard (UCT):
#   - UCT: selecciona o filho com maior valor UCB1 (balanço exploração/explotação
#     determinístico via fórmula matemática)
#   - ε-greedy: com probabilidade ε escolhe um filho aleatório (exploração pura),
#     com probabilidade 1-ε escolhe o filho com mais visitas (explotação pura)
#
# Trade-offs:
#   + Mais simples de sintonizar (só 1 parâmetro: ε)
#   + Exploração mais "surpresa" — pode descobrir ramos que UCT ignora
#   - Menos eficiente que UCT em espaços de jogo grandes
#   - ε fixo não se adapta ao longo da árvore (UCT adapta-se naturalmente)
# ---------------------------------------------------------------------------

EPSILON = 0.2  # probabilidade de exploração aleatória (típico: 0.1 a 0.3)


def best_child_greedy(node):
    """
    Política ε-greedy para selecção:
      - Com prob. ε: escolhe filho aleatório (exploração)
      - Com prob. 1-ε: escolhe filho com mais visitas (explotação)
    """
    if random.random() < EPSILON:
        return random.choice(node.children)
    return max(node.children, key=lambda n: n.visits)


# ---------------------------------------------------------------------------
# Verificação de vitória imediata
# ---------------------------------------------------------------------------

def check_immediate_win(board, move, player):
    test = copy.deepcopy(board)
    apply_move(test, move, player)
    if move[0] == 'pop':
        return check_winner_after_pop(test, player) == player
    return check_winner(test, player)


# ---------------------------------------------------------------------------
# Ordenação de movimentos (igual ao MCTS standard — partilha a heurística)
# ---------------------------------------------------------------------------

def order_moves(moves, board, player):
    opponent = next_player(player)
    wins, blocks, good_drops, neutral_drops, pops = [], [], [], [], []

    for move in moves:
        move_type, col = move
        if move_type == 'pop' and is_bad_pop(board, col, player):
            continue
        if check_immediate_win(board, move, player):
            wins.append(move)
        elif check_immediate_win(board, move, opponent):
            blocks.append(move)
        elif move_type == 'drop':
            test = copy.deepcopy(board)
            apply_move(test, move, player)
            score = evaluate_board(test, player)
            if score >= 10:
                good_drops.append((score, move))
            else:
                neutral_drops.append(move)
        else:
            pops.append(move)

    good_drops.sort(key=lambda x: -x[0])
    good_sorted = [m for _, m in good_drops]
    neutral_drops.sort(key=lambda m: COLUMN_PRIORITY.index(m[1]) if m[1] < 7 else 99)

    return wins + blocks + good_sorted + neutral_drops + pops


# ---------------------------------------------------------------------------
# Selecção ε-greedy
# ---------------------------------------------------------------------------

def select_eg(node):
    """
    Desce a árvore usando ε-greedy em vez de UCT.
    Para nos nós não totalmente expandidos, devolve o nó para expansão.
    """
    while node.children:
        moves = get_valid_moves(node.state, node.player)
        tried = [ch.move for ch in node.children]
        if len(tried) < len(moves):
            return node  # nó não totalmente expandido → expandir
        node = best_child_greedy(node)
    return node


# ---------------------------------------------------------------------------
# Expansão
# ---------------------------------------------------------------------------

def expand_eg(node):
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

    return node


# ---------------------------------------------------------------------------
# Simulação (rollout) — igual ao MCTS standard
# ---------------------------------------------------------------------------

def simulate_eg(state, player):
    board = copy.deepcopy(state)
    current = player

    for _ in range(MAX_SIMULATE_TURNS):
        moves = get_valid_moves(board, current)
        if not moves:
            return None

        opponent = next_player(current)

        win = next((m for m in moves if check_immediate_win(board, m, current)), None)
        if win:
            apply_move(board, win, current)
            return current

        block = next((m for m in moves if check_immediate_win(board, m, opponent)), None)

        if block:
            chosen = block
        else:
            candidates = [m for m in moves
                          if not (m[0] == 'pop' and is_bad_pop(board, m[1], current))]
            if not candidates:
                candidates = moves

            scored = []
            for m in candidates:
                test = copy.deepcopy(board)
                apply_move(test, m, current)
                s = evaluate_board(test, current)
                s += random.uniform(-5, 5)
                scored.append((s, m))

            scored.sort(key=lambda x: -x[0])
            top = scored[:3]
            chosen = random.choice(top)[1]

        apply_move(board, chosen, current)

        move_type = chosen[0]
        if move_type == 'pop':
            winner = check_winner_after_pop(board, current)
            if winner:
                return winner
        else:
            if check_winner(board, current):
                return current

        current = next_player(current)

    return None


# ---------------------------------------------------------------------------
# Backpropagation (igual ao MCTS standard)
# ---------------------------------------------------------------------------

def backpropagate_eg(node, winner, root_player):
    while node:
        node.visits += 1
        if winner is not None and winner != node.player:
            node.wins += 1
        node = node.parent


# ---------------------------------------------------------------------------
# Entrada principal do algoritmo ε-greedy
# ---------------------------------------------------------------------------

def mcts_epsilon_greedy(board, player, iterations=1000, epsilon=EPSILON):
    """
    MCTS com política de selecção ε-greedy.

    Parâmetros:
      iterations — número de simulações
      epsilon    — probabilidade de exploração aleatória [0, 1]
                   0.0 = sempre escolhe o melhor (puramente ganancioso)
                   1.0 = sempre aleatório (exploração pura)
                   0.2 = valor padrão recomendado

    Comparação com MCTS standard (UCT):
      UCT usa uma fórmula matemática para balancear exploração/explotação
      de forma contínua e adaptativa. ε-greedy usa uma decisão binária:
      ou explora aleatoriamente ou explora o melhor nó conhecido.
      ε-greedy é mais simples mas menos adaptativo ao longo da árvore.
    """
    global EPSILON
    EPSILON = epsilon  # permite configurar epsilon por chamada

    root = Node(copy.deepcopy(board), player)

    for _ in range(iterations):
        node = select_eg(root)
        node = expand_eg(node)
        winner = simulate_eg(node.state, node.player)
        backpropagate_eg(node, winner, player)

    if not root.children:
        moves = get_valid_moves(board, player)
        if moves:
            ordered = order_moves(moves, board, player)
            return ordered[0] if ordered else moves[0]
        return None

    # Decisão final: escolhe sempre o filho com mais visitas (explotação pura)
    best = max(root.children, key=lambda n: n.visits)
    return best.move