from lark import Lark, Transformer, Tree, Token
from typing import Callable
from automata import Nfa, ALPHABET

state_index = 1


def fresh_state_closure() -> Callable[[], int]:
    state_index = 0

    def increment() -> int:
        nonlocal state_index
        state_index += 1
        return state_index

    return increment


fresh_state = fresh_state_closure()

regex_lexer = Lark(
    r"""
    regex: primitive
         | exp
         // | "(" regex ")"
         // | "[" range "]"
         // | regex_or
         // | regex_concat
         // | regex_kleene

    exp: regex_or
       | term

    term: regex_concat
        | fact

    fact: regex_kleene
        | parens

    parens: "(" regex ")"

    regex_or: regex "|" regex
    regex_concat: regex regex
    regex_kleene: regex "*"

    range: primitive "-" primitive

    primitive: DIGIT
             | LETTER

    %import common.LETTER -> LETTER
    %import common.DIGIT -> DIGIT
    %import common.ESCAPED_STRING -> STRING
    %import common.WS
    %ignore WS
""",
    start="regex",
)


def nodes_to_nfas(*items: Tree[Nfa]) -> list[Nfa]:
    children: list[Nfa | Tree[Nfa]] = [t.children[0] for t in items]
    nfas: list[Nfa] = []
    for mayb_tree in children:
        while isinstance(mayb_tree, Tree):
            assert len(mayb_tree.children) == 1
            mayb_tree = mayb_tree.children[0]
        nfas.append(mayb_tree)
    return nfas


class RegexParser(Transformer):
    def regex_kleene(self, items: list[Tree[Nfa]]) -> Nfa:
        assert len(items) == 1
        sub_nfa = nodes_to_nfas(*items)[0]
        assert len(sub_nfa.final_set) == 1

        sub_nfa_end = sub_nfa.final_set.pop()
        new_start = fresh_state()
        new_end = fresh_state()

        trans_fn = sub_nfa.trans_fn.copy()
        trans_fn.update({(new_start, ""): set([new_end, sub_nfa.start])})
        trans_fn.update({(sub_nfa_end, ""): set([sub_nfa.start, new_end])})
        result = Nfa(
            new_start,
            sub_nfa.state_set.union(set([new_start, new_end])),
            sub_nfa.alphabet,
            trans_fn,
            set([new_end]),
        )
        return result

    def regex_concat(self, items: list[Tree[Nfa]]) -> Nfa:
        assert len(items) == 2
        left, right = nodes_to_nfas(*items)
        assert len(left.final_set) == 1
        assert len(right.final_set) == 1

        new_start = fresh_state()
        new_end = fresh_state()

        trans_fn = left.trans_fn.copy()
        trans_fn.update(right.trans_fn)
        trans_fn.update({(new_start, ""): set([left.start])})
        trans_fn.update({(left.final_set.pop(), ""): set([right.start])})
        trans_fn.update({(right.final_set.pop(), ""): set([new_end])})
        result = Nfa(
            new_start,
            right.state_set.union(left.state_set).union(set([new_start, new_end])),
            left.alphabet,
            trans_fn,
            set([new_end]),
        )
        return result

    def regex_or(self, items: list[Tree[Nfa]]) -> Nfa:
        assert len(items) == 2
        left, right = nodes_to_nfas(*items)
        assert len(left.final_set) == 1
        assert len(right.final_set) == 1

        new_start = fresh_state()
        new_end = fresh_state()
        new_state_set = right.state_set.union(left.state_set).union(
            set({new_start, new_end})
        )

        trans_fn = left.trans_fn.copy()
        trans_fn.update(right.trans_fn)
        trans_fn.update({(new_start, ""): set([right.start, left.start])})
        trans_fn.update({(right.final_set.pop(), ""): set([new_end])})
        trans_fn.update({(left.final_set.pop(), ""): set([new_end])})
        result = Nfa(
            new_start,
            new_state_set,
            left.alphabet,
            trans_fn,
            set([new_end]),
        )
        return result

    def primitive(self, items: list[Token]) -> Nfa:
        # 1 -a-> 2
        states = [fresh_state(), fresh_state()]
        char = items[0][0]
        trans_fn: dict[tuple[int | str, str], set[int | str]] = {
            (states[0], char): set([states[1]])
        }
        result = Nfa(states[0], set(states), ALPHABET, trans_fn, set([states[1]]))
        return result
