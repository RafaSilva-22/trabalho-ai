"""Arvore de decisao ID3 para atributos numericos e categoricos.

Este modulo implementa uma versao simples do ID3:
- calcula entropia das classes;
- testa varios splits por atributo, com thresholds ou valores categoricos;
- escolhe o split com maior ganho de informacao;
- cria a arvore recursivamente.
"""

import math
from collections import Counter


class Leaf:
    """Folha da arvore: guarda a classe final prevista."""

    def __init__(self, label):
        self.label = label


class NumericDecisionNode:
    """No interno numerico: divide exemplos usando um threshold."""

    def __init__(self, attribute, threshold, left, right, majority_label):
        self.attribute = attribute
        self.threshold = threshold
        self.left = left
        self.right = right
        self.majority_label = majority_label


DecisionNode = NumericDecisionNode


class CategoricalDecisionNode:
    """No interno categorico: divide exemplos por valor exato do atributo."""

    def __init__(self, attribute, branches, majority_label):
        self.attribute = attribute
        self.branches = branches
        self.majority_label = majority_label


def entropy(rows, target):
    """Calcula a impureza dos exemplos em relacao a classe alvo."""
    total = len(rows)
    counts = Counter(row[target] for row in rows)
    value = 0.0

    for count in counts.values():
        probability = count / total
        value -= probability * math.log2(probability)

    return value


def majority_label(rows, target):
    """Devolve a classe mais frequente num conjunto de exemplos."""
    return Counter(row[target] for row in rows).most_common(1)[0][0]


def candidate_thresholds(rows, attribute):
    """Cria thresholds entre valores consecutivos de um atributo numerico."""
    values = sorted({row[attribute] for row in rows})
    return [(values[i] + values[i + 1]) / 2 for i in range(len(values) - 1)]


def information_gain(rows, attribute, threshold, target):
    """Mede quanto um split numerico reduz a entropia dos exemplos."""
    parent_entropy = entropy(rows, target)
    left = [row for row in rows if row[attribute] <= threshold]
    right = [row for row in rows if row[attribute] > threshold]

    if not left or not right:
        return 0.0

    total = len(rows)
    children_entropy = (
        len(left) / total * entropy(left, target)
        + len(right) / total * entropy(right, target)
    )
    return parent_entropy - children_entropy


def categorical_information_gain(rows, attribute, target):
    """Mede quanto um split por categorias reduz a entropia dos exemplos."""
    parent_entropy = entropy(rows, target)
    groups = {}

    for row in rows:
        groups.setdefault(row[attribute], []).append(row)

    if len(groups) < 2:
        return 0.0

    total = len(rows)
    children_entropy = sum(
        len(group) / total * entropy(group, target)
        for group in groups.values()
    )
    return parent_entropy - children_entropy


def best_numeric_split(rows, attributes, target):
    """Procura o melhor atributo e threshold para dividir os exemplos."""
    best_attribute = None
    best_threshold = None
    best_gain = 0.0

    for attribute in attributes:
        for threshold in candidate_thresholds(rows, attribute):
            gain = information_gain(rows, attribute, threshold, target)
            if gain > best_gain:
                best_gain = gain
                best_attribute = attribute
                best_threshold = threshold

    return best_attribute, best_threshold, best_gain


def best_categorical_split(rows, attributes, target):
    """Procura o melhor atributo categorico para dividir os exemplos."""
    best_attribute = None
    best_gain = 0.0

    for attribute in attributes:
        gain = categorical_information_gain(rows, attribute, target)
        if gain > best_gain:
            best_gain = gain
            best_attribute = attribute

    return best_attribute, best_gain


def build_tree(
    rows,
    attributes,
    target="class",
    min_gain=1e-9,
    max_depth=None,
    depth=0,
    split_mode="numeric",
):
    """Constroi a arvore de decisao de forma recursiva."""
    if split_mode not in {"numeric", "categorical"}:
        raise ValueError("split_mode deve ser 'numeric' ou 'categorical'.")

    labels = {row[target] for row in rows}
    fallback_label = majority_label(rows, target)

    # Se todos os exemplos ja tem a mesma classe, chegamos a uma folha perfeita.
    if len(labels) == 1:
        return Leaf(next(iter(labels)))

    # Para se a profundidade acabou ou se nao ha atributos para testar.
    if not attributes or (max_depth is not None and depth >= max_depth):
        return Leaf(fallback_label)

    if split_mode == "categorical":
        attribute, gain = best_categorical_split(rows, attributes, target)
        if attribute is None or gain <= min_gain:
            return Leaf(fallback_label)

        branches = {}
        remaining_attributes = [
            candidate for candidate in attributes
            if candidate != attribute
        ]
        values = sorted({row[attribute] for row in rows})

        for value in values:
            matching_rows = [row for row in rows if row[attribute] == value]
            branches[value] = build_tree(
                matching_rows,
                remaining_attributes,
                target=target,
                min_gain=min_gain,
                max_depth=max_depth,
                depth=depth + 1,
                split_mode=split_mode,
            )

        return CategoricalDecisionNode(attribute, branches, fallback_label)

    attribute, threshold, gain = best_numeric_split(rows, attributes, target)
    if attribute is None or gain <= min_gain:
        return Leaf(fallback_label)

    # Divide os exemplos de acordo com a pergunta escolhida.
    left_rows = [row for row in rows if row[attribute] <= threshold]
    right_rows = [row for row in rows if row[attribute] > threshold]

    left = build_tree(
        left_rows,
        attributes,
        target=target,
        min_gain=min_gain,
        max_depth=max_depth,
        depth=depth + 1,
        split_mode=split_mode,
    )
    right = build_tree(
        right_rows,
        attributes,
        target=target,
        min_gain=min_gain,
        max_depth=max_depth,
        depth=depth + 1,
        split_mode=split_mode,
    )

    return NumericDecisionNode(attribute, threshold, left, right, fallback_label)


def predict(tree, row):
    """Percorre a arvore e devolve a classe prevista para uma amostra."""
    if isinstance(tree, Leaf):
        return tree.label

    if isinstance(tree, CategoricalDecisionNode):
        value = row[tree.attribute]
        branch = tree.branches.get(value)
        if branch is None:
            return tree.majority_label
        return predict(branch, row)

    if row[tree.attribute] <= tree.threshold:
        return predict(tree.left, row)
    return predict(tree.right, row)


def accuracy(tree, rows, target="class"):
    """Calcula a percentagem de previsoes corretas."""
    if not rows:
        return 0.0

    correct = sum(1 for row in rows if predict(tree, row) == row[target])
    return correct / len(rows)


def print_tree(tree, indent=""):
    """Imprime a arvore em formato legivel no terminal."""
    if isinstance(tree, Leaf):
        print(f"{indent}-> {tree.label}")
        return

    if isinstance(tree, CategoricalDecisionNode):
        print(f"{indent}{tree.attribute}?")
        for value in sorted(tree.branches):
            print(f"{indent}  {value}:")
            print_tree(tree.branches[value], indent + "    ")
        return

    print(f"{indent}{tree.attribute} <= {tree.threshold:.3f}?")
    print(f"{indent}  sim:")
    print_tree(tree.left, indent + "    ")
    print(f"{indent}  nao:")
    print_tree(tree.right, indent + "    ")
