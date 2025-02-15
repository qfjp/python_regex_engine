# Example Regex Engine

## Install & Run

Use `poetry` to create a virtualenv and download all dependencies:

```
pip install poetry
poetry shell
python main.py
```

You can use your own regular expression and test strings:
```
# Matches
python main.py "(0a|b)" "0a"

# Doesn't match
python main.py "(0a|b)" "0b"
```

The alphabet defaults to "0ab"

## How it works

Below, I will roughly follow how I arranged the lecture on regular
expressions, while also providing the relevant functions in the code.

A regular expression is equivalent to some finite automaton. First,
this parses a regular expression with the `parser` module. Using
syntax directed translation, the regular expression is converted to an
NFA with the following rules:

$$
\pmb{\textit{Define:}} \textit{An } \text{NFA} \textit{ is a 5-tuple},
\left< q_0, \Sigma, Q, \delta, F\right>, \text{where:}
$$
  * $q_0$ is the *start state*,
  * $\Sigma$ is the *alphabet*,
  * $Q$ is the *set of states*,
  * $\delta: \mathcal{P}(Q) \times \Sigma \rightarrow \mathcal{P}(Q)$,
    is the *transition function*,
  * and $F$ is the *set of accepting states*.
$$

NFAs are represented with `automata.Nfa`. In the constructor
(`automata.Nfa.__init__`) you can see the arguments provided
correspond to the values of the 5-tuple. The transition function
$\delta$ is represented with a dictionary, but the `Nfa` class also
provides various methods roughly corresponding to $\delta$ or
$\delta^*$. The only working method corresponding to the algorithms
discussed is `automata.Nfa.accepts`, which takes a string and
determines if the NFA accepts or not. At some point `regex_reduce`
will be implemented to convert an NFA back to an equivalent regular expression,
though not necessarily the same one used to contruct it. If the
alphabet $\Sigma$ is small, you can also print out the NFA to
visualize the transition function. Letting $\Sigma = \set{a, b, 0}$:

```
> python main.py "0|b" "b"
ε-NFA
=====
                     |                 ε |                 a |                 b |                 0
---------------------+-------------------+-------------------+-------------------+-------------------
                   0 |             <{0}> |             <{0}> |             <{0}> |             <{0}>
                 <1> |           <{<0>}> |           <{<0>}> |           <{<0>}> | <{<0>, <2>, <6>}>
                 <2> |      <{<0>, <6>}> |           <{<0>}> |           <{<0>}> |           <{<0>}>
                 <3> |           <{<0>}> |           <{<0>}> | <{<0>, <4>, <6>}> |           <{<0>}>
                 <4> |      <{<0>, <6>}> |           <{<0>}> |           <{<0>}> |           <{<0>}>
               -><5> | <{<0>, <1>, <3>}> |           <{<0>}> | <{<0>, <4>, <6>}> | <{<0>, <2>, <6>}>
                *<6> |           <{<0>}> |           <{<0>}> |           <{<0>}> |           <{<0>}>

The test string matches
```

\pmb{\textit{Define:}} \textit{A} \text{ regular expression
}\textit{(over some alphabet } \Sigma\textit{) is defined recursively
as follows:}
$$
  * $\emptyset$ is a regular expression matching nothing.
  * $\varepsilon$ is a regular expression matching the empty string,
    i.e. `""`
  * $a$ where $a \in \Sigma$ is a regular expression matching the
    character $a$
In the code, these correspond to `parser.RegexParser.primitive`

Let R & S be regular expressions:
  * $RS$ is a regular expression (concatenation). This is
    `parser.RegexParser.regex_concat`
  * $R|S$ is a regular expression (union). This is
    `parser.RegexParser.regex_or`
  * $R^*$ is a regular expression (kleene star). This is
    `parser.RegexParser.regex_kleene`

