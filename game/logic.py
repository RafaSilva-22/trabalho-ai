ROWS = 6
COLS = 7


def is_valid_move(board, col):
    return board[0][col] == ' '


def check_winner(board, player):
    # Check horizontal
    for row in range(ROWS):
        for col in range(COLS - 3):
            if all(board[row][col + i] == player for i in range(4)):
                return True

    # Check vertical
    for col in range(COLS):
        for row in range(ROWS - 3):
            if all(board[row + i][col] == player for i in range(4)):
                return True

    # Check diagonal (bottom-left to top-right)
    for row in range(3, ROWS):
        for col in range(COLS - 3):
            if all(board[row - i][col + i] == player for i in range(4)):
                return True

    # Check diagonal (top-left to bottom-right)
    for row in range(ROWS - 3):
        for col in range(COLS - 3):
            if all(board[row + i][col + i] == player for i in range(4)):
                return True

    return False


def check_winner_after_pop(board, player):
    """
    Regra 1 do PopOut: se um pop cria 4-em-linha para ambos os jogadores,
    quem fez o pop ganha. Devolve o vencedor ('X', 'O') ou None.
    """
    opponent = 'O' if player == 'X' else 'X'
    player_wins = check_winner(board, player)
    opponent_wins = check_winner(board, opponent)

    if player_wins:
        return player  # quem fez o pop ganha sempre, mesmo que o adversário também faça 4
    if opponent_wins:
        return opponent
    return None


def is_board_full(board):
    """Verifica se o tabuleiro está completamente cheio."""
    return all(board[0][col] != ' ' for col in range(COLS))


def boards_equal(b1, b2):
    """Compara dois tabuleiros célula a célula."""
    return all(b1[r][c] == b2[r][c] for r in range(ROWS) for c in range(COLS))


class GameState:
    """
    Gere o histórico de estados para detectar repetições (Regra 3).
    Uso: instanciar no início do jogo e chamar register() após cada jogada.
    """

    def __init__(self):
        self.history = []  # lista de snapshots do tabuleiro

    def register(self, board):
        snapshot = [row[:] for row in board]
        self.history.append(snapshot)

    def is_threefold_repetition(self, board):
        """
        Regra 3: se o estado actual apareceu 3 ou mais vezes no histórico,
        qualquer jogador pode declarar empate.
        """
        count = sum(1 for snap in self.history if boards_equal(snap, board))
        return count >= 3