"""
A parser for LETREC and part of INFERRED.

TODO: extend to other languages.

Author: Thomas Bauwens
Date: 2023-01-24
"""
from inferred import *
import re

typed = False


def stringToExpression(program: str):
    global typed
    typed = COLON in program  # It causes less clutter to do this than to recursively pass the same argument over and over.
    return parse(lex(program))


LET     = "let"
LETREC  = "letrec"
IN      = "in"
PROC    = "proc"
IF      = "if"
THEN    = "then"
ELSE    = "else"
LEFT    = "("
RIGHT   = ")"
ZEROTEST = "zero?"
MINUS   = "-"
COMMA   = ","
COLON   = ":"

KEYWORDS = {LET, LETREC, IN, PROC, IF, THEN, ELSE, LEFT, RIGHT, ZEROTEST, MINUS, COMMA, COLON}

TARGET_TO_HEADS = {   # When searching for this thing -> this thing means you have to find it a second time.
    IN    : {LET, LETREC},
    THEN  : {IF},
    ELSE  : {THEN},
    RIGHT : {LEFT},  # Note that commas by themselves never appear without their parenthesis.
    COMMA : {MINUS},
}
HEAD_TO_TARGET = {
    LET    : IN,
    LETREC : IN,
    IF     : THEN,
    THEN   : ELSE,
    LEFT   : RIGHT,
    MINUS  : COMMA
}


def flatten(l: list):
    flattened = []
    for nested in l:
        flattened.extend(nested)
    return flattened


def lex(s: str) -> list:
    """
    Converts a program string into a flat list of meaningful tokens.
    """
    s = s.replace("\n", " ")
    s = s.split(" ")
    s = flatten([re.compile(r"([(),:])").split(t) for t in s])
    s = [t for t in s if t != ""]
    return s


def findUnmatched(tokens: list, target: str):
    """
    Finds the first unmatched occurrence of the target token in the list.
    """
    heads = TARGET_TO_HEADS.get(target, set())

    stack = 0
    for idx, token in enumerate(tokens):
        if token == target:
            if not stack:
                return idx
            else:
                stack -= 1
        elif token in heads:
            stack += 1

    raise ValueError(f"Target not found: {target} in {tokens}")


def pop0many(lst: list, amount: int):
    """
    In-place pop(0) many times.
    """
    return [lst.pop(0) for _ in range(amount)]


def nextGroup(tokens: list, target: str) -> list:
    """
    Combines findUnmatched with pop0many.
    The returned subexpression is removed entirely from the given list.
    """
    index      = findUnmatched(tokens, target)
    expression = pop0many(tokens, index)
    tokens.pop(0)  # pop the target
    return expression


def parse(lexed: list) -> Expression:
    """
    Turn a list of tokens into an expression.

    More precisely: pops the first token off the list. If this token is a keyword, then all following tokens that belong
    to its subexpression are popped from the list too and parsed recursively. Else, it is just an identifier/number.
    """
    if not lexed:
        raise ValueError("Cannot parse empty expression.")

    final_exp: Expression = None

    head = lexed.pop(0)
    if head == PROC:
        if typed:
            leftparen, var, colon, var_type, rightparen = pop0many(lexed, 5)
            body = lexed

            final_exp = ProcExpTyped(var, parse(body), parseType(var_type))
        else:
            leftparen, var, rightparen = pop0many(lexed, 3)
            body = lexed

            final_exp = ProcExp(var, parse(body))

    elif head == LET:
        var, equal = pop0many(lexed, 2)
        val_body = nextGroup(lexed, IN)
        let_body = lexed

        final_exp = LetExp(var,
            parse(val_body),
            parse(let_body)
        )

    elif head == LETREC:
        if typed:
            return_type, name, leftparen, var, colon, var_type, rightparen, equal = pop0many(lexed, 8)
            proc_body = nextGroup(lexed, IN)
            let_body = lexed

            final_exp = LetrecExpTyped(name, var,
                parse(proc_body),
                parse(let_body),
                parseType(return_type), parseType(var_type)
            )
        else:
            name, leftparen, var, rightparen, equal = pop0many(lexed, 5)
            proc_body = nextGroup(lexed, IN)
            let_body = lexed

            final_exp = LetrecExp(name, var,
                parse(proc_body),
                parse(let_body)
            )

    elif head == IF:
        condition = nextGroup(lexed, THEN)
        then_body = nextGroup(lexed, ELSE)
        else_body = lexed

        final_exp = IfExp(
            parse(condition),
            parse(then_body),
            parse(else_body)
        )

    elif head == MINUS:
        lexed.pop(0)  # (

        diff1_body = nextGroup(lexed, COMMA)
        diff2_body = nextGroup(lexed, RIGHT)

        final_exp = DiffExp(
            parse(diff1_body),
            parse(diff2_body)
        )

    elif head == LEFT:
        call_body = nextGroup(lexed, RIGHT)
        operator_exp = parse(call_body)  # There is no comma that stops the operator and starts the operand. We let the operator consume as much as it can recognise.
        operand_exp  = parse(call_body)

        final_exp = CallExp(operator_exp, operand_exp)

    elif head == ZEROTEST:
        lexed.pop(0)  # (
        tested_body = nextGroup(lexed, RIGHT)

        final_exp = IsZeroExp(parse(tested_body))

    else:  # Identifier or number
        if head.isnumeric():
            final_exp = ConstExp(head)
        elif head.isidentifier():
            final_exp = VarExp(head)
        else:
            raise ValueError(f"Weird symbol found: {head}")

    return final_exp


def parseType(annotation: str) -> Type:
    """
    We assume type annotations cannot be more than a single token. Hence, something like "int -> bool" isn't a valid
    annotation, but could still be the type of an expression.
    """
    if annotation == "int":
        return BaseType("int")
    elif annotation == "bool":
        return BaseType("bool")
    elif annotation == "?":
        return UnknownType()
    else:
        raise ValueError(f"Unknown type annotation: {annotation}")


if __name__ == "__main__":
    s = """
    letrec
        ? foo (x: ?) = if zero?(x)
            then 1
            else -(x, (foo -(x,1)))
    in foo
    """
    # s = """
    # (proc (x: ?) x 1)
    # """
    # s = """
    # let p = proc (x) proc (y) -(x,y)
    # in ((p 1) 2)
    # """
    # s = """
    # (proc (p) (p 1) proc (x) x)
    # """
    # s = """
    # (proc (x) x 1)
    # """

    from printer import *
    print(expression__repr__(stringToExpression(s)))
