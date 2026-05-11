from game.board import ROWS, COLS
from game.logic import check_winner
import copy

# Pontuação por janela de N peças do mesmo jogador
SCORE_4 = 100000   # vitória
SCORE_3 = 50       # 3 em linha com espaço livre
SCORE_2 = 10       # 2 em linha com espaço livre
SCORE_CENTER = 4   # bónus de coluna central

# Penalizações
PENALTY_OPP_3 = -80   # adversário tem 3 em linha
PENALTY_OPP_2 = -8
PENALTY_BAD_POP = -30  # pop que destrói as próprias peças


def score_window(window, player, opponent):
    """Pontua uma janela de 4 células."""
    p_count = window.count(player)
    o_count = window.count(opponent)
    empty = window.count(' ')

    if p_count == 4:
        return SCORE_4
    if o_count == 4:
        return -SCORE_4

    score = 0
    if p_count == 3 and empty == 1:
        score += SCORE_3
    elif p_count == 2 and empty == 2:
        score += SCORE_2

    if o_count == 3 and empty == 1:
        score += PENALTY_OPP_3
    elif o_count == 2 and empty == 2:
        score += PENALTY_OPP_2

    return score


def evaluate_board(board, player):
    """
    Avalia o tabuleiro do ponto de vista de 'player'.
    Pontuação positiva = bom para player, negativa = mau.
    """
    opponent = 'O' if player == 'X' else 'X'
    score = 0

    # Bónus por peças na coluna central (3)
    center_col = [board[r][COLS // 2] for r in range(ROWS)]
    score += center_col.count(player) * SCORE_CENTER

    # Horizontal
    for r in range(ROWS):
        for c in range(COLS - 3):
            window = [board[r][c + i] for i in range(4)]
            score += score_window(window, player, opponent)

    # Vertical
    for c in range(COLS):
        for r in range(ROWS - 3):
            window = [board[r + i][c] for i in range(4)]
            score += score_window(window, player, opponent)

    # Diagonal ↗
    for r in range(3, ROWS):
        for c in range(COLS - 3):
            window = [board[r - i][c + i] for i in range(4)]
            score += score_window(window, player, opponent)

    # Diagonal ↘
    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            window = [board[r + i][c + i] for i in range(4)]
            score += score_window(window, player, opponent)

    return score


def is_bad_pop(board, col, player):
    """
    Verifica se um pop é prejudicial:
    - Só tem 1 peça na coluna (pop desperdiça um turno)
    - Destrói uma sequência própria de 2+ peças na base
    """
    # Contar peças do player na coluna
    col_pieces = [board[r][col] for r in range(ROWS) if board[r][col] == player]
    if len(col_pieces) <= 1:
        return True  # pop com 1 peça é geralmente mau

    # Verificar se ao fazer pop quebramos 2+ em linha horizontalmente na base
    base_row = ROWS - 1
    # Simular o pop: a base passa a ser a peça de cima
    # Penalizar se a peça na base fazia parte de uma sequência horizontal
    left = sum(1 for c in range(col - 1, max(-1, col - 3), -1)
               if c >= 0 and board[base_row][c] == player)
    right = sum(1 for c in range(col + 1, min(COLS, col + 3))
                if board[base_row][c] == player)
    if left + right >= 2:  # estava ligada a pelo menos 1 peça horizontalmente
        return True

    return False