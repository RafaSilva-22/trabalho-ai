class Node:
    def __init__(self, state, player, parent=None, move=None):
        self.state = state
        self.player = player
        self.parent = parent
        self.move = move
        self.children = []
        self.visits = 0
        self.wins = 0
