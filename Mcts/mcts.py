import math
import random
import copy

from Mcts.node import Node
from auxiliares.helpers import get_valid_moves, apply_move, next_player
from game.logic import check_winner, check_winner_after_pop
from Mcts.heuristica import evaluate_board, is_bad_pop

MAX_SIMULATE_TURNS = 100
COLUMN_PRIORITY = [3, 2, 4, 1, 5, 0, 6]


# ---------------------------------------------------------------------------
# UCT
# ---------------------------------------------------------------------------

def uct(node, c=1.4):
    if node.visits == 0:
        return float("inf")
    return (node.wins / node.visits) + c * math.sqrt(
        math.log(node.parent.visits) / node.visits
    )


# ---------------------------------------------------------------------------
# Selecção
# ---------------------------------------------------------------------------

def select(node, c=1.4):
    while node.children:
        moves = get_valid_moves(node.state, node.player)
        tried = [ch.move for ch in node.children]
        if len(tried) < len(moves):
            return node
        node = max(node.children, key=lambda n: uct(n, c))
    return node


# ---------------------------------------------------------------------------
# Verificação de vitória imediata (suporta pop simultâneo)
# ---------------------------------------------------------------------------

def check_immediate_win(board, move, player):
    test = copy.deepcopy(board)
    apply_move(test, move, player)
    move_type = move[0]
    if move_type == 'pop':
        # Regra 1: quem faz o pop ganha se ambos ficam com 4-em-linha
        return check_winner_after_pop(test, player) == player
    return check_winner(test, player)


# ---------------------------------------------------------------------------
# Ordenação de movimentos
# ---------------------------------------------------------------------------

def order_moves(moves, board, player):
    """
    Ordena e filtra movimentos por qualidade:
    1. Vitória imediata
    2. Bloqueio de vitória adversária
    3. Drops que prolongam sequências
    4. Drops centrais
    5. Pops razoáveis
    6. Pops maus (descartados)
    """
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
# Expansão
# ---------------------------------------------------------------------------

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

    return node


# ---------------------------------------------------------------------------
# Simulação (rollout heurístico)
# ---------------------------------------------------------------------------

def simulate(state, player):
    """
    Rollout heurístico com suporte à Regra 1 (pop simultâneo).
    """
    board = copy.deepcopy(state)
    current = player

    for _ in range(MAX_SIMULATE_TURNS):
        moves = get_valid_moves(board, current)
        if not moves:
            return None  # empate

        opponent = next_player(current)

        # 1. Vitória imediata
        win = next((m for m in moves if check_immediate_win(board, m, current)), None)
        if win:
            apply_move(board, win, current)
            return current

        # 2. Bloquear vitória adversária
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

        # Verificar vitória com suporte ao pop simultâneo
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
# Backpropagation
#
# Cada nó representa um estado do jogo. node.player é quem vai jogar
# A PARTIR desse estado — ou seja, quem jogou para CHEGAR a este estado
# foi node.parent.player.
#
# O UCT calcula wins/visits para decidir qual filho explorar. Esse rácio
# deve reflectir "quão bom foi jogar a jogada que levou a este nó", ou seja,
# deve ser incrementado quando node.parent.player (quem jogou) ganhou.
# Como node.parent.player != node.player, a condição simplifica para:
# winner != node.player.
#
# Exemplo:
#   Raiz: player=X (X vai jogar)
#   Filho A: player=O (O vai jogar, significa X jogou para chegar aqui)
#   Se X ganhou → filho A deve ter wins++ (foi X que jogou para aqui)
#   winner='X' != node.player='O' → condição correcta
# ---------------------------------------------------------------------------

def backpropagate(node, winner, root_player):
    while node:
        node.visits += 1
        if winner is not None and winner != node.player:
            node.wins += 1
        node = node.parent


# ---------------------------------------------------------------------------
# MCTS principal
# ---------------------------------------------------------------------------

def mcts(board, player, iterations=1000, c=1.4):
    """
    Implementação única de MCTS. O comportamento varia com os parâmetros:

      iterations — número de simulações. Mais iterações = decisões mais
                   informadas, mas mais tempo de computação.

      c          — constante de exploração UCT (Upper Confidence Bound).
                   Valor alto (ex: 1.4 ≈ √2): explora mais ramos novos.
                   Valor baixo (ex: 0.8): aprofunda os ramos já prometedores.

    Exemplos de uso no modo PC vs PC:
      X (explorador):  mcts(board, player, iterations=1000, c=1.4)
      O (focado):      mcts(board, player, iterations=2000, c=0.8)
    """
    root = Node(copy.deepcopy(board), player)

    for _ in range(iterations):
        node = select(root, c)
        node = expand(node)
        winner = simulate(node.state, node.player)
        backpropagate(node, winner, player)

    if not root.children:
        moves = get_valid_moves(board, player)
        if moves:
            ordered = order_moves(moves, board, player)
            return ordered[0] if ordered else moves[0]
        return None

    best = max(root.children, key=lambda n: n.visits)
    return best.move