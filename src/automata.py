from collections import defaultdict
import string

# ALPHABET = string.printable
ALPHABET = "ab0"


class Nfa:
    # State is for states, U is for alphabet
    # A DFA is a 5-tuple: (q_0, Q, Σ, δ, F)
    def __init__(
        self,
        start: int | str,
        state_set: set[int | str],
        alphabet: str,
        trans_fn: dict[tuple[int | str, str], set[int | str]],
        final_set: set[int | str],
    ):
        assert state_set.issuperset(final_set)
        assert start in state_set
        self.start = start
        self.state_set = state_set
        self.alphabet = alphabet
        self.trans_fn = defaultdict(lambda: set([0]), trans_fn)
        self.final_set = final_set

    def delta(self, state: int | str, char: str) -> set[int | str]:
        char = "" if char == "ε" else char
        try:
            possibilities = [
                self.trans_fn[(state_p, char)]
                for state_p in self.eps_close(set([state]))
            ]
            return self.eps_close(set().union(*possibilities))
        except KeyError:
            return set([0])

    def delta_sets(self, cur_states: set[int | str], char: str) -> set[int | str]:
        init: set[int] = set()
        for state in cur_states:
            init.union(self.delta(state, char))
        possibilities = [self.delta(state, char) for state in cur_states]
        return self.eps_close(set().union(*possibilities))

    def delta_star(self, input: str) -> set[int | str]:
        cur_state_set = self.eps_close(set([self.start]))
        for char in input:
            cur_state_set = self.delta_sets(cur_state_set, char)
        return self.eps_close(cur_state_set)

    def accepts(self, input: str) -> bool:
        return self.delta_star(input).intersection(self.final_set) != set()

    def eps_close(self, states: set[int | str]) -> set[int | str]:
        stack = states.copy()
        result: set[int | str] = states.copy()
        visited: set[int | str] = set()
        while len(stack) != 0:
            state = stack.pop()
            result.add(state)
            if state not in visited:
                stack = stack.union(self.trans_fn[(state, "")])
            visited.add(state)
        return result

    def regex_reduce(self) -> str:
        new_start = "start"
        new_end = "fin"
        new_trans_fn: dict[tuple[int | str, str], set[int | str]]
        new_trans_fn = {
            (str(state), char): set([str(x) for x in self.trans_fn[(state, char)]])
            for state, char in self.trans_fn
        }
        new_states = self.state_set.union(set([new_start, new_end]))
        # Add in epsilon transitions to final state
        for final_state in self.final_set:
            new_trans_fn[(final_state, "")] = set([new_end])
        # Add in epsilon transition to start
        new_trans_fn[(new_start, "")] = set([self.start])
        clean_nfa = Nfa(
            new_start, new_states, self.alphabet, new_trans_fn, set([new_end])
        )
        print(clean_nfa)
        return ""

    def __str__(self) -> str:
        # Just calculating the epsilon closures fills in the values
        _ = [self.eps_close(val) for val in list(self.trans_fn.values())]

        longest_state_set_name_len = max(
            [len(str(self.eps_close(val))) for val in self.trans_fn.values()]
        )

        # Make room for start and final annotations
        first_format = "{:>" + str(longest_state_set_name_len + 3) + "} | "
        # The rest are sized smaller
        format = "{:>" + str(longest_state_set_name_len) + "} | "

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

        has_zero = False  # Just in case we need a null state
        for state in self.state_set:
            transitions = [self.delta(state, char) for char in "ε" + self.alphabet]
            if set([0]) in transitions:
                has_zero = True
            state_str = state if state not in self.final_set else "*{}".format(state)
            state_str = state_str if state != self.start else "->{}".format(state_str)
            result_lst.append(
                line_format.format(state_str, *[str(x) for x in transitions])
            )
        if has_zero:
            result_lst.insert(
                2, line_format.format(0, *[str(set([0])) for _ in "ε" + self.alphabet])
            )
        return "\n".join(result_lst)


def tests() -> None:
    trans_fn: dict[tuple[int | str, str], set[int | str]] = {
        (1, "a"): set([1]),
        (1, "b"): set([1]),
        (1, "c"): set([1]),
    }
    nfa = Nfa(1, set([1, 2, 3]), "abc", trans_fn, set([1]))
    print(nfa.delta_sets(set([1, 2]), "a"))
    print(nfa.accepts("abca"))
    nfa.regex_reduce()
    print(nfa)


def main() -> None:
    tests()


# main()
