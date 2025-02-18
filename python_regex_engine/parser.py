from typing import Callable

from lark import Lark, Token, Transformer, Tree

from python_regex_engine.automata import ALPHABET, Nfa
from python_regex_engine.monoids import Set, Sum

state_index = 1


def fresh_state_closure() -> Callable[[], Sum]:
    state_index = Sum(0)

    def increment() -> Sum:
        nonlocal state_index
        state_index += 1
        return state_index

    return increment


fresh_state = fresh_state_closure()

regex_lexer = Lark(
    r"""
    regex: primitive
         | exp
         // | "[" range "]"

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


def nodes_to_nfas(*items: Tree[Nfa[Sum]]) -> list[Nfa[Sum]]:
    children: list[Nfa[Sum] | Tree[Nfa[Sum]]] = [t.children[0] for t in items]
    nfas: list[Nfa[Sum]] = []
    for mayb_tree in children:
        while isinstance(mayb_tree, Tree):
            assert len(mayb_tree.children) == 1
            mayb_tree = mayb_tree.children[0]
        nfas.append(mayb_tree)
    return nfas


class RegexParser(Transformer):
    def regex_kleene(self, items: list[Tree[Nfa[Sum]]]) -> Nfa[Sum]:
        assert len(items) == 1
        sub_nfa = nodes_to_nfas(*items)[0]
        assert len(sub_nfa.final_set) == 1

        sub_nfa_end = sub_nfa.final_set.pop()
        new_start = fresh_state()
        new_end = fresh_state()

        trans_fn = sub_nfa.trans_fn.copy()
        trans_fn.update({(new_start, ""): Set([new_end, sub_nfa.start])})
        trans_fn.update({(sub_nfa_end, ""): Set([sub_nfa.start, new_end])})
        result: Nfa[Sum] = Nfa(
            new_start,
            sub_nfa.state_set.union(Set({new_start, new_end})),
            sub_nfa.alphabet,
            trans_fn,
            Set({new_end}),
        )
        return result

    def regex_concat(self, items: list[Tree[Nfa[Sum]]]) -> Nfa[Sum]:
        assert len(items) == 2
        left, right = nodes_to_nfas(*items)
        assert len(left.final_set) == 1
        assert len(right.final_set) == 1

        new_start = fresh_state()
        new_end = fresh_state()

        trans_fn = left.trans_fn.copy()
        trans_fn.update(right.trans_fn)
        trans_fn.update({(new_start, ""): Set([left.start])})
        trans_fn.update({(left.final_set.pop(), ""): Set([right.start])})
        trans_fn.update({(right.final_set.pop(), ""): Set([new_end])})
        result: Nfa[Sum] = Nfa(
            new_start,
            right.state_set.union(left.state_set).union(Set({new_start, new_end})),
            left.alphabet,
            trans_fn,
            Set([new_end]),
        )
        return result

    def regex_or(self, items: list[Tree[Nfa[Sum]]]) -> Nfa[Sum]:
        assert len(items) == 2
        left, right = nodes_to_nfas(*items)
        assert len(left.final_set) == 1
        assert len(right.final_set) == 1

        new_start = fresh_state()
        new_end = fresh_state()
        new_state_set = right.state_set.union(left.state_set).union(
            Set({new_start, new_end})
        )

        trans_fn = left.trans_fn.copy()
        trans_fn.update(right.trans_fn)
        trans_fn.update({(new_start, ""): Set([right.start, left.start])})
        trans_fn.update({(right.final_set.pop(), ""): Set([new_end])})
        trans_fn.update({(left.final_set.pop(), ""): Set([new_end])})
        result: Nfa[Sum] = Nfa(
            new_start,
            new_state_set,
            left.alphabet,
            trans_fn,
            Set([new_end]),
        )
        return result

    def primitive(self, items: list[Token]) -> Nfa[Sum]:
        # 1 -a-> 2
        start = fresh_state()
        end = fresh_state()
        char = items[0][0]
        trans_fn: dict[tuple[Sum, str], Set[Sum]] = {(start, char): Set({end})}
        result: Nfa[Sum] = Nfa(start, Set({start, end}), ALPHABET, trans_fn, Set({end}))
        return result
