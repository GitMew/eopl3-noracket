"""
IMPLICIT-REFS, which is EXPLICIT-REFS without newref/setref/deref, and instead
with `let`/`letrec` using the store, a `set` for variables, and copy-on-call semantics.

(The `set` is particularly useful for variables that were captured in a closure;
not so much for procedure arguments, as they are copied.)

Author: Thomas Bauwens
Date: 2023-01-06
"""
from explicit_refs import *

DenVal = Reference


####################
### Environments ###
####################
# Environments that stayed the same:
#   EmptyEnvironment
#   ExtendEnvironment

class EnvlessProcEnvironment(Environment):

    def __init__(self, procname: str, procvar: str, procbody: "Expression", tail: Environment):
        self.lookupvar = procname
        self.envless_proc_var  = procvar
        self.envless_proc_body = procbody
        self.tail = tail

    def lookup(self, var: str) -> DenVal:
        if self.lookupvar == var:
            return THE_STORE.store(THE_STORE.new(), ProcVal(self.envless_proc_var, self.envless_proc_body, self))
        else:
            return self.tail.lookup(var)


###################
### Expressions ###
###################
# Expressions that stayed the same:
#   ConstExp
#   ProcExp
#   DiffExp
#   IsZeroExp
#   IfExp

class VarExp(Expression):

    def __init__(self, var: str):
        self.var = var

    def value_of(self, env: Environment) -> ExpVal:
        return THE_STORE.load(env.lookup(self.var))


class LetExp(Expression):

    def __init__(self, var: str, val_exp: Expression, body_exp: Expression):
        self.var = var
        self.val_exp = val_exp
        self.body_exp = body_exp

    def value_of(self, env: Environment) -> ExpVal:
        return self.body_exp.value_of(
            ExtendEnvironment(self.var, THE_STORE.store(THE_STORE.new(), self.val_exp.value_of(env)), env)
        )


class LetrecExp(Expression):

    def __init__(self, procname: str, procvar: str, procbody: Expression, letbody: Expression):
        self.procname = procname
        self.procvar = procvar
        self.procbody = procbody
        self.letbody = letbody

    def value_of(self, env: Environment) -> ExpVal:
        return self.letbody.value_of(
            EnvlessProcEnvironment(self.procname, self.procvar, self.procbody, env)
        )


# TODO:
#   1. Does just redefining apply_procedure in this file redefine it in letrec.py's CallExp? Probably not.
#   2. If I put this apply_procedure after CallExp's redefinition, is it still used in the redefinition, or does the imported function get precedent?
def apply_procedure(proc: ProcVal, arg: ExpVal) -> ExpVal:
    return proc.body.value_of(
        ExtendEnvironment(proc.var, THE_STORE.store(THE_STORE.new(), arg), proc.closed_env)
    )


class CallExp(Expression):

    def __init__(self, operator_exp: Expression, operand_exp: Expression):
        self.operator = operator_exp
        self.operand = operand_exp

    def value_of(self, env: Environment) -> ExpVal:
        return apply_procedure(ProcVal.cast(self.operator.value_of(env)), self.operand.value_of(env))


class SetExp(Expression):
    """
    Unlike EXPLICIT-REFS, the argument isn't a pointer, but simply an identifier.
    """

    def __init__(self, var: str, value_exp: Expression):
        self.var = var
        self.value_exp = value_exp

    def value_of(self, env: Environment) -> ExpVal:
        THE_STORE.store(env.lookup(self.var), self.value_exp.value_of(env))
        return IntVal(-1_000_002)


if __name__ == "__main__":
    prog = Program(
        LetExp("y", ConstExp(74),
               LetExp("p", ProcExp("x", DiffExp(VarExp("y"), VarExp("x"))),
                      CallExp(VarExp("p"), ConstExp(5)))
               ),
        EmptyEnvironment()
    )

    print(IntVal.cast(prog.value_of_program()).value)
    print(THE_STORE)