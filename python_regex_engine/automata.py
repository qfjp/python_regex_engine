from collections import defaultdict
from typing import TypeAlias, TypeVar, Self

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

    def __eq__(self, other: object) -> bool:
        """
        Equivalence is checked by converting to DFAs
        and checking using the symmetric difference
        """
        if not isinstance(other, Nfa):
            return False
        if self.alphabet != other.alphabet:
            return False
        return self.to_dfa() == other.to_dfa()
        pass

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
            state_str = str(state) if state not in self.final_set else "*{}".format(state)
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

        self._remove_unreachable()

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

    def _remove_unreachable(self) -> None:
        visited: Set[State[T]] = Set()
        state_stack = Set({self.start})
        while len(state_stack) > 0:
            cur_state = state_stack.pop()
            if cur_state in visited:
                continue
            visited.add(cur_state)
            for char in self.alphabet:
                state_stack.add(self.delta(cur_state, char))
        unreachables = self.state_set - visited
        self.state_set = visited
        for state in unreachables:
            for char in self.alphabet:
                self.trans_fn.pop((state, char))
        self.final_set = self.final_set.intersection(self.state_set)

    def minimize(self) -> "Dfa[T]":
        distinguishable_matrix: dict[tuple[State[T], State[T]], bool] = dict()
        state_list = list(self.state_set)
        for state_i in state_list:
            for state_j in state_list[0 : state_list.index(state_i)]:
                i_in_final = state_i in self.final_set
                j_in_final = state_j in self.final_set
                init_dist = (i_in_final and not j_in_final) or (
                    j_in_final and not i_in_final
                )
                distinguishable_matrix[(state_i, state_j)] = init_dist

        def distinguishable(state_i: State[T], state_j: State[T]) -> bool:
            if state_i == state_j:
                return False
            try:
                return distinguishable_matrix[(state_i, state_j)]
            except KeyError:
                return distinguishable_matrix[(state_j, state_i)]

        changed = True
        while changed:
            changed = False
            for state_i, state_j in distinguishable_matrix:
                if distinguishable(state_i, state_j) or state_i == state_j:
                    continue
                for char in self.alphabet:
                    if distinguishable(
                        self.delta(state_i, char), self.delta(state_j, char)
                    ):
                        try:
                            distinguishable_matrix[(state_i, state_j)]
                            distinguishable_matrix[(state_i, state_j)] = True
                        except KeyError:
                            distinguishable_matrix[(state_j, state_i)] = True
                        changed = True
        rename = {i: i for i in self.state_set}
        rename.update(
            {
                i: j
                for i, j in distinguishable_matrix
                if not distinguishable_matrix[i, j]
            }
        )
        # The above can't handle 3 or more states equivalent
        # to each other, so we need to recursively set the renaming
        # dictionary
        for key in rename:
            prev_val = key
            cur_val = rename[key]
            while prev_val != cur_val:
                prev_val = cur_val
                cur_val = rename[cur_val]
            rename[key] = cur_val

        new_start = rename[self.start]
        new_trans_fn = {
            (rename[i], c): rename[self.delta(i, c)] for i, c in self.trans_fn
        }
        new_states = Set([rename[i] for i in self.state_set])
        new_finals = Set([rename[i] for i in self.final_set])

        return Dfa(new_start, new_states, self.alphabet, new_trans_fn, new_finals)

    def reindex(self) -> "Dfa[int]":
        new_names = {state: i for i, state in enumerate(self.state_set)}
        new_start = new_names[self.start]
        new_states: State[int] = Set([new_names[state] for state in self.state_set])
        new_trans_fn = {
            (new_names[i], c): new_names[self.delta(i, c)] for i, c in self.trans_fn
        }
        new_finals: State[int] = Set([new_names[i] for i in self.final_set])
        return Dfa(new_start, new_states, self.alphabet, new_trans_fn, new_finals)

    def __eq__(self: Self, other: object) -> bool:
        """
        We can verify equality using the symmetric difference:
            A△ B = (A - B) ∪ (B - A)
        The symmetric difference of the languages of the two DFAs
        is empty iff the two DFAs are equivalent. This can be
        checked by doing a depth/breadth first search on the product
        construction; if no final states are found then the DFAs are
        equivalent.
        """
        if not isinstance(other, Dfa):
            return False
        if self.alphabet != other.alphabet:
            return False
        # Instead of doing a depth/breadth first search, just
        # construct the product and minimize.
        new_start = (self.start, other.start)
        new_finals: Set[tuple[State[T], State[T]]] = Set(
            [
                (f1, s2)  # type: ignore[arg-type]
                for f1 in self.final_set
                for s2 in other.state_set - other.final_set
            ]
        ) + Set(
            [  # type: ignore[arg-type]
                (s1, f2)
                for s1 in self.state_set - self.final_set
                for f2 in other.final_set
            ]
        )
        new_state_set: Set[tuple[State[T], State[T]]] = Set(
            [(s1, s2) for s1 in self.state_set for s2 in other.state_set]
        )
        new_trans: dict[
            tuple[tuple[State[T], State[T]], str], tuple[State[T], State[T]]
        ] = {
            ((s1, s2), char): (self.delta(s1, char), other.delta(s2, char))
            for s1 in self.state_set
            for s2 in other.state_set
            for char in self.alphabet
        }
        sym_diff: Dfa[tuple[State[T], State[T]]] = Dfa(
            new_start, new_state_set, self.alphabet, new_trans, new_finals
        ).minimize()
        # If the symmetric difference has one state and it is
        # non-accepting, then the language of the symmetric difference
        # is empty and the DFAs are the same
        return len(sym_diff.state_set) == 1 and len(sym_diff.final_set) == 0

    def __neg__(self) -> "Dfa[T]":
        """
        Negating a DFA is just swapping final states to nonfinal and vice versa.
        """
        return Dfa(
            self.start,
            self.state_set,
            self.alphabet,
            self.trans_fn,
            self.state_set - self.final_set,
        )

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
            state_str = str(state) if state not in self.final_set else "*{}".format(state)
            state_str = state_str if state != self.start else "->{}".format(state_str)
            result_lst.append(
                line_format.format(state_str, *[str(x) for x in transitions])
            )
        return "\n".join(result_lst)
