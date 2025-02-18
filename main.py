import sys

from lark import Tree

from python_regex_engine.automata import Nfa
from python_regex_engine.parser import RegexParser, regex_lexer


def main() -> None:
    text = "(0|a)b(aba)*"
    test_str = "0baba"
    try:
        text = sys.argv[1]
    except IndexError:
        print("No regex given, defaulting to '{}'".format(text))
        print()
    try:
        test_str = sys.argv[2]
    except IndexError:
        print("No test string given, defaulting to '{}'".format(test_str))
        print()

    tree = regex_lexer.parse(text)
    result_mayb_tree = RegexParser().transform(tree)
    while isinstance(result_mayb_tree, Tree):
        result_mayb_tree = result_mayb_tree.children[0]
    result: Nfa[str] = result_mayb_tree
    print("ε-NFA")
    print("=====")
    print(result)
    print()
    print(
        "The test string matches (NFA)"
        if result.accepts(test_str)
        else "The test string doesn't match (NFA)"
    )
    print()
    dfa = result.to_dfa()
    print("DFA")
    print("===")
    print(dfa)
    print()
    print(
        "The test string matches (DFA)"
        if dfa.accepts(test_str)
        else "The test string doesn't match (DFA)"
    )


if __name__ == "__main__":
    main()
