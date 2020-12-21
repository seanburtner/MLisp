################ Lispy: Scheme Interpreter in Python

## (c) Peter Norvig, 2010-16; See http://norvig.com/lispy.html
## Edited to enable 64 bit int overflow so that the OCaml tests pass

from __future__ import division, print_function
import math
import operator as op

################ Types

Symbol = str  # A Lisp Symbol is implemented as a Python str
List = list  # A Lisp List is implemented as a Python list
Number = (int, float)  # A Lisp Number is implemented as a Python int or float

################ Parsing: parse, tokenize, and read_from_tokens


def parse(program):
    "Read a Scheme expression from a string."
    return read_from_tokens(tokenize(program))


def tokenize(s):
    "Convert a string into a list of tokens."
    return s.replace("(", " ( ").replace(")", " ) ").split()


def read_from_tokens(tokens):
    "Read an expression from a sequence of tokens."
    if len(tokens) == 0:
        raise SyntaxError("unexpected EOF while reading")
    token = tokens.pop(0)
    if "(" == token:
        L = []
        while tokens[0] != ")":
            L.append(read_from_tokens(tokens))
        tokens.pop(0)  # pop off ')'
        return L
    elif ")" == token:
        raise SyntaxError("unexpected )")
    else:
        return atom(token)


def atom(token):
    "Numbers become numbers; every other token is a symbol."
    try:
        return int(token)
    except ValueError:
        try:
            return float(token)
        except ValueError:
            return Symbol(token)


################ Environments


MAXINT = (2 ** 63) - 1


# from https://stackoverflow.com/a/7771363
def int_overflow(val):
    if not -MAXINT - 1 <= val <= MAXINT:
        val = (val + (MAXINT + 1)) % (2 * (MAXINT + 1)) - MAXINT - 1
    return val


def add(a, b):
    return int_overflow(a + b)


def sub(a, b):
    return int_overflow(a - b)


def mul(a, b):
    return int_overflow(a * b)


def div(a, b):
    return int_overflow(a / b)


def standard_env():
    "An environment with some Scheme standard procedures."
    env = Env()
    # env.update(vars(math))  # sin, cos, sqrt, pi, ...
    env.update(
        {
            "+": add,
            "-": sub,
            "*": mul,
            "/": div,
            ">": op.gt,
            "<": op.lt,
            ">=": op.ge,
            "<=": op.le,
            "=": op.eq,
            "abs": abs,
            "append": op.add,
            "apply": apply,
            "begin": lambda *x: x[-1],
            "car": lambda x: x[0],
            "cdr": lambda x: x[1:],
            "cons": lambda x, y: [x] + y,
            "eq?": op.is_,
            "expt": pow,
            "equal?": op.eq,
            "length": len,
            "list": lambda *x: list(x),
            "list?": lambda x: isinstance(x, list),
            "map": map,
            "max": max,
            "min": min,
            "not": op.not_,
            "null?": lambda x: x == [],
            "number?": lambda x: isinstance(x, Number),
            "procedure?": callable,
            "print": print,
            "round": round,
            "symbol?": lambda x: isinstance(x, Symbol),
        }
    )
    return env


class Env(dict):
    "An environment: a dict of {'var':val} pairs, with an outer Env."

    def __init__(self, parms=(), args=(), outer=None):
        self.update(zip(parms, args))
        self.outer = outer

    def find(self, var):
        "Find the innermost Env where var appears."
        return self if (var in self) else self.outer.find(var)


global_env = standard_env()

################ Interaction: A REPL


def repl(prompt="lis.py> "):
    "A prompt-read-eval-print loop."
    while True:
        val = eval(parse(raw_input(prompt)))
        if val is not None:
            print(lispstr(val))


def lispstr(exp):
    "Convert a Python object back into a Lisp-readable string."
    if isinstance(exp, List):
        return "(" + " ".join(map(lispstr, exp)) + ")"
    else:
        return str(exp)


################ Procedures


class Procedure(object):
    "A user-defined Scheme procedure."

    def __init__(self, parms, body, env):
        self.parms, self.body, self.env = parms, body, env

    def __call__(self, *args):
        return eval(self.body, Env(self.parms, args, self.env))


################ eval


def eval(x, env=global_env):
    "Evaluate an expression in an environment."
    if isinstance(x, Symbol):  # variable reference
        return env.find(x)[x]
    elif not isinstance(x, List):  # constant literal
        return x
    elif x[0] == "quote":  # (quote exp)
        (_, exp) = x
        return exp
    elif x[0] == "if":  # (if test conseq alt)
        (_, test, conseq, alt) = x
        exp = conseq if eval(test, env) else alt
        return eval(exp, env)
    elif x[0] == "define":  # (define var exp)
        (_, var, exp) = x
        env[var] = eval(exp, env)
    elif x[0] == "set!":  # (set! var exp)
        (_, var, exp) = x
        env.find(var)[var] = eval(exp, env)
    elif x[0] == "lambda":  # (lambda (var...) body)
        (_, parms, body) = x
        return Procedure(parms, body, env)
    else:  # (proc arg...)
        proc = eval(x[0], env)
        args = [eval(exp, env) for exp in x[1:]]
        return proc(*args)


def eval_program(program):
    "evaluates a program string and returns a lis.py-readable string"
    return lispstr(eval(parse(program)))
