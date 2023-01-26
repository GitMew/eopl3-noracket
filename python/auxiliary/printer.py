"""
A printer for LETREC.

Really, this should be done by methods. However, I am afraid of cluttering the subclasses of Expression with
support methods that are not needed for the interpreter to work. This is one of those cases where a functional
language with "type classes" (Haskell) or "traits" (Rust) shines, since they allow adding methods to existing classes
in other files.

TODO: extend to other languages.

Author: Thomas Bauwens
Date: 2023-01-24
"""
from inferred import *


TAB = "\t"


def expression__repr__(exp: Expression, indent=0) -> str:
    if isinstance(exp, VarExp):
        return exp.var
    elif isinstance(exp, ConstExp):
        return str(exp.const)
    elif isinstance(exp, ProcExp):
        if isinstance(exp, ProcExpTyped):
            return "proc (" + exp.var + ": " + type__repr__(exp.tv) + ") " + expression__repr__(exp.body_exp, indent+1)
        else:
            return "proc (" + exp.var + ") " + expression__repr__(exp.body_exp, indent+1)
    elif isinstance(exp, CallExp):
        return "({" + expression__repr__(exp.operator, indent+1) + "} " + expression__repr__(exp.operand, indent+1) + ")"
    elif isinstance(exp, LetExp):
        return "let " + exp.var + " = " + expression__repr__(exp.val_exp, indent+1) + \
            "\n" + indent*TAB + "in " + expression__repr__(exp.body_exp, indent+1)
    elif isinstance(exp, LetrecExp):
        if isinstance(exp, LetrecExpTyped):
            return "letrec " + type__repr__(exp.tr) + " " + exp.procname + " (" + exp.procvar + ": " + type__repr__(exp.tv) + ") = " + expression__repr__(exp.procbody, indent+1) + \
                "\n" + indent*TAB + "in " + expression__repr__(exp.letbody, indent+1)
        else:
            return "letrec " + exp.procname + " (" + exp.procvar + ") = " + expression__repr__(exp.procbody, indent+1) + \
                "\n" + indent*TAB + "in " + expression__repr__(exp.letbody, indent+1)
    elif isinstance(exp, IsZeroExp):
        return "zero?(" + expression__repr__(exp.exp, indent+1) + ")"
    elif isinstance(exp, IfExp):
        return "if " + expression__repr__(exp.cond_exp, indent+1) + \
            "\n" + indent*TAB + "then " + expression__repr__(exp.true_exp, indent+1) + \
            "\n" + indent*TAB + "else " + expression__repr__(exp.false_exp, indent+1)
    elif isinstance(exp, DiffExp):
        return "{" + expression__repr__(exp.exp1, indent+1) + " - " + expression__repr__(exp.exp2, indent+1) + "}"
    else:
        return "{PRINTER}"


def type__repr__(type_to_print: Type) -> str:
    if isinstance(type_to_print, ProcType):
        part1 = type__repr__(type_to_print.t1)
        if isinstance(type_to_print.t1, ProcType):
            part1 = "(" + part1 + ")"

        part2 = type__repr__(type_to_print.t2)
        if isinstance(type_to_print.t2, ProcType):
            part2 = "(" + part2 + ")"

        return part1 + " -> " + part2

    elif isinstance(type_to_print, BaseType):
        return type_to_print.name

    elif isinstance(type_to_print, TypeVariable):
        return f"t_{type_to_print.num}"

    elif isinstance(type_to_print, UnknownType):
        return "?"


def rule__repr__(rule: Rule):
    return "(" + type__repr__(rule.head) + ", " + type__repr__(rule.body) + ")"


def substitution__repr__(sub: Substitution):
    return "{\n" + "".join(["\t" + rule__repr__(r) + "\n" for r in sub.rules]) + "}"


if __name__ == "__main__":
    sub = Substitution()

    "t1 -> (int -> t1) = bool -> (t3 -> t4)"
    lhs = ProcType(TypeVariable(1), ProcType(BaseType("int"), TypeVariable(1)))
    rhs = ProcType(BaseType("bool"), ProcType(TypeVariable(3), TypeVariable(4)))

    lhs.unify(rhs, sub)
    print(substitution__repr__(sub))