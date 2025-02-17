from collections import defaultdict
from typing import TypeAlias, TypeVar

from pymonad.monoid import Monoid  # type: ignore[import-untyped]

from python_regex_engine.monoids import Set, Sum

# ALPHABET = string.printable
ALPHABET = "ab0"

T = TypeVar("T")
State: TypeAlias = Monoid[T]  # type: ignore[no-any-unimported]


class Nfa[T]:
    def __init__(
        self,
        start: State[T],
        state_set: Set[State[T]],
        alphabet: str,
        trans_fn: dict[tuple[State[T], str], Set[State[T]]],
        final_set: Set[State[T]],
    ):
        """An NFA is a 5-tuple: (q_0, Q, Σ, δ, F)."""
        assert state_set.issuperset(final_set)
        assert start in state_set
        self.start = start
        self.state_set = state_set
        self.alphabet = alphabet
        self.trans_fn = defaultdict(lambda: Set({start.identity_element()}), trans_fn)
        self.final_set = final_set

        # defaultdict is used, so calculating values will fill in
        # missing items. We need ε's and ε-closures
        _ = [self.trans_fn[(state, "")] for state in self.state_set]
        _ = [self.eps_close(val) for val in list(self.trans_fn.values())]
        visible_states: Set[T] = Set().union(*list(self.trans_fn.values()))
        if (
            start.identity_element() in visible_states
            and start.identity_element() not in state_set
        ):
            self.state_set = self.state_set.union(Set({start.identity_element()}))
        assert self.state_set.issuperset(visible_states)

    def delta(self, state: State[T], char: str) -> Set[State[T]]:
        char = "" if char == "ε" else char
        possibilities = [
            self.trans_fn[(state_p, char)] for state_p in self.eps_close(Set({state}))
        ]
        return self.eps_close(Set().union(*possibilities))

    def delta_sets(self, cur_states: Set[State[T]], char: str) -> Set[State[T]]:
        init: set[int] = Set()
        for state in cur_states:
            init.union(self.delta(state, char))
        possibilities = [self.delta(state, char) for state in cur_states]
        return self.eps_close(Set().union(*possibilities))

    def delta_star(self, state: State[T], input: str) -> Set[State[T]]:
        cur_state_set = self.eps_close(Set([state]))
        for char in input:
            cur_state_set = self.delta_sets(cur_state_set, char)
        return self.eps_close(cur_state_set)

    def accepts(self, input: str) -> bool:
        return self.delta_star(self.start, input).intersection(self.final_set) != Set()

    def eps_close(self, states: Set[State[T]]) -> Set[State[T]]:
        stack = states.copy()
        result: Set[State[T]] = states.copy()
        visited: Set[State[T]] = Set()
        while len(stack) != 0:
            state = stack.pop()
            if state in self.state_set:  # Should only be triggered if state == ∅
                result.add(state)
            else:
                continue
            if state not in visited:
                stack = stack.union(self.trans_fn[(state, "")])
            visited.add(state)
        return result

    def to_dfa(self) -> "Dfa[Set[T]]":
        new_states: Set[Set[T]] = Set()
        new_start = self.eps_close(Set(self.start))
        state_stack: Set[Set[T]] = Set({Set(), new_start})
        while len(state_stack) != 0:
            cur_state = state_stack.pop()
            new_states.add(cur_state)
            for char in self.alphabet:
                child_state = self.eps_close(self.delta_sets(cur_state, char))
                if child_state not in new_states:
                    state_stack.add(child_state)
        nested_transition_keys = [
            [(state, char) for char in self.alphabet] for state in new_states
        ]
        transition_keys = [
            state_and_char
            for sublist in nested_transition_keys
            for state_and_char in sublist
        ]
        new_trans_fn: dict[tuple[Set[T], str], Set[Set[T]]] = {
            (state, char): self.delta_sets(state, char)
            for state, char in transition_keys
        }
        new_finals: Set[Set[T]] = Set(
            {
                state
                for state in new_states
                if state.intersection(self.final_set) != Set()
            }
        )
        return Dfa(new_start, new_states, self.alphabet, new_trans_fn, new_finals)

    def regex_reduce(self) -> str:
        new_start = "start"
        new_end = "fin"
        new_trans_fn: dict[tuple[State[T], str], Set[State[T]]]
        new_trans_fn = {
            (str(state), char): Set([str(x) for x in self.trans_fn[(state, char)]])
            for state, char in self.trans_fn
        }
        new_states = self.state_set.union(Set({new_start, new_end}))
        # Add in epsilon transitions to final state
        for final_state in self.final_set:
            new_trans_fn[(final_state, "")] = Set({new_end})
        # Add in epsilon transition to start
        new_trans_fn[(new_start, "")] = Set({self.start})
        clean_nfa: Nfa[T] = Nfa(
            new_start, new_states, self.alphabet, new_trans_fn, Set({new_end})
        )
        print(clean_nfa)
        return ""

    def __str__(self) -> str:
        """
        TODO: This can certainly be simplified with Dfa.__str__
        """

        longest_state_or_set_name_len = max(
            [len(str(self.eps_close(val))) for val in self.trans_fn.values()]
            + [len(str(state)) for state in self.state_set]
        )

        # Make room for start and final annotations
        first_format = "{:>" + str(longest_state_or_set_name_len + 3) + "} | "
        # The rest are sized smaller
        format = "{:>" + str(longest_state_or_set_name_len) + "} | "

        line_formats = [format for _ in "ε" + self.alphabet[1:]]
        line_formats.insert(0, format)
        line_formats.insert(0, first_format)
        line_format = "".join(line_formats)[:-3]

        # Build the return values
        result_lst = [line_format.format("", "ε", *self.alphabet)]

        pipe_lengths = []  # To find where to put "+" in separator
        prev_i = -1
        for i, x in enumerate(result_lst[0]):
            if x == "|":
                pipe_lengths.append((i - 1) - prev_i)
                prev_i = i
        sep_string = "+".join(["-" * p for p in pipe_lengths])
        pipe_lengths.append(len(result_lst[0]) - len(sep_string))
        result_lst.append("+".join(["-" * p for p in pipe_lengths]))

        for state in self.state_set:
            transitions = [self.delta(state, char) for char in "ε" + self.alphabet]
            state_str = state if state not in self.final_set else "*{}".format(state)
            state_str = state_str if state != self.start else "->{}".format(state_str)
            result_lst.append(
                line_format.format(state_str, *[str(x) for x in transitions])
            )
        return "\n".join(result_lst)


class Dfa[T]:
    def __init__(
        self,
        start: State[T],
        state_set: Set[State[T]],
        alphabet: str,
        trans_fn: dict[tuple[State[T], str], State[T]],
        final_set: Set[State[T]],
    ):
        """
        A DFA is a 5-tuple: (q_0, Q, Σ, δ, F).

        The primary definitional difference between
        DFA's and NFA's is that in an NFA, Im(δ): Set[T],
        while for a DFA Im(δ): T

        We can't use inheritance because of the types :-(
        """
        assert state_set.issuperset(final_set)
        assert start in state_set
        self.start = start
        self.state_set = state_set
        self.alphabet = alphabet
        self.trans_fn = trans_fn
        self.final_set = final_set

        # A plain dict is used, as a DFA must be complete on
        # initialization
        visible_states: Set[T] = Set(list(self.trans_fn.values()))
        assert self.state_set.issuperset(visible_states)

    def delta(self, state: State[T], char: str) -> State[T]:
        """
        DFAs don't have ε transitions, so this is a straightforward
        dict -> function
        """
        return self.trans_fn[state, char]

    def delta_star(self, state: State[T], input: str) -> State[T]:
        cur_state = state
        for char in input:
            cur_state = self.delta(cur_state, char)
        return cur_state

    def accepts(self, input: str) -> bool:
        return self.delta_star(self.start, input) in self.final_set

    def __str__(self) -> str:
        """
        TODO: This can certainly be simplified with Nfa.__str__
        """
        longest_state_name_len = max([len(str(val)) for val in self.state_set])

        # Make room for start and final annotations
        first_format = "{:>" + str(longest_state_name_len + 3) + "} | "
        # The rest are sized smaller
        format = "{:>" + str(longest_state_name_len) + "} | "

        line_formats = [format for _ in self.alphabet[1:]]
        line_formats.insert(0, format)
        line_formats.insert(0, first_format)
        line_format = "".join(line_formats)[:-3]

        # Build the return values
        result_lst = [line_format.format("", *self.alphabet)]

        pipe_lengths = []  # To find where to put "+" in separator
        prev_i = -1
        for i, x in enumerate(result_lst[0]):
            if x == "|":
                pipe_lengths.append((i - 1) - prev_i)
                prev_i = i
        sep_string = "+".join(["-" * p for p in pipe_lengths])
        pipe_lengths.append(len(result_lst[0]) - len(sep_string))
        result_lst.append("+".join(["-" * p for p in pipe_lengths]))

        for state in self.state_set:
            transitions = [self.delta(state, char) for char in self.alphabet]
            state_str = state if state not in self.final_set else "*{}".format(state)
            state_str = state_str if state != self.start else "->{}".format(state_str)
            result_lst.append(
                line_format.format(state_str, *[str(x) for x in transitions])
            )
        return "\n".join(result_lst)
