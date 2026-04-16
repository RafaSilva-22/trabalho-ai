import random
import math

from Mcts.node import Node


#Select functions from game.py
def select(node):
    while node.children:
        node = max(node.children, key=lambda n: n.wins / n.visits + (2 * (2 * math.log(node.visits) / n.visits) ** 0.5))
    return node