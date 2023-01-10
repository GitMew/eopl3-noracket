"""
LETREC interpreter, but in Python, clearly superior to Racket.

Note: the goal of the course is to implement more powerful programming language features than those available to
implement them. One could object that this Pythonic implementation uses OOP (even polymorphism!), which is highly
advanced already. However, the EOPL code not only uses Racket's lambda feature, but it uses pattern matching with
abstract datatypes. That means Racket has a mechanism in place for polymorphism, and hence, it is equally advanced.

TODO: I think Java might be an even better language to teach this in. The reason is that you have the OOP and typing
      like Python, but you can neglect "self.", which makes the code even cleaner.

Author: Thomas Bauwens
Date: 2023-01-06 (took me less than an hour to write this up)
"""
from abc import abstractmethod, ABC
from typing import Self  # New in Python 3.11. Very useful! https://stackoverflow.com/questions/75036613/automatically-use-subclass-type-in-method-signature


#########################
### Expression Values ###
#########################
class ExpVal(ABC):
    @classmethod
    def cast(cls, val: "ExpVal") -> Self:
        """
        Assert that the given value is of the class on which this method is called, and
        cast it to that value so that its fields can be accessed without type unsafety.

        Since Python's compiler doesn't require this, we can technically ignore this kind of assertion.
        It's not correct though, and Racket has a bunch of functions like "expval->intval" to do this.
        """
        if cls == val.__class__:
            return val
        else:
            raise TypeError(f"Tried to cast {val.__class__.__name__} to {cls.__name__}!")

class IntVal(ExpVal):
    def __init__(self, value: int):
        self.value = value
    def __repr__(self):
        return f"IntVal({self.value})"

class BoolVal(ExpVal):
    def __init__(self, value: bool):
        self.value = value
    def __repr__(self):
        return f"BoolVal({self.value})"

class ProcVal(ExpVal):
    def __init__(self, var: str, body: "Expression", closed_env: "Environment"):
        self.var = var
        self.body = body
        self.closed_env = closed_env
    def __repr__(self):
        return f"ProcVal({self.var})"

DenVal = ExpVal


####################
### Environments ###
####################
class Environment(ABC):

    @abstractmethod
    def lookup(self, var: str) -> DenVal:
        pass


class EmptyEnvironment(Environment):
    def lookup(self, var: str) -> DenVal:
        raise ValueError(f"Failed to find {var} in environment.")


class ExtendEnvironment(Environment):

    def __init__(self, var: str, val: DenVal, tail: Environment):
        self.var = var
        self.val = val
        self.tail = tail

    def lookup(self, var: str) -> DenVal:
        if self.var == var:
            return self.val
        else:
            return self.tail.lookup(var)


class EnvlessProcEnvironment(Environment):
    """
    A recursive function needs to have itself in its own scope (which is represented by a closure).
    You say: "Okay, so create a ProcVal and add it to the environment before closing."
    No! That ProcVal needs to have ITSELF in its closed environment in turn. To break the cycle, you have to store an
    environmentless proc. Then, when you look it up, this class:
        1. Constructs a ProcVal on the fly
        2. Passes ITSELF -- the on-the-fly ProcVal creating environment -- to the ProcVal, instead of its tail.
    """

    def __init__(self, procname: str, procvar: str, procbody: "Expression", tail: Environment):
        self.lookupvar = procname
        self.envless_proc_var  = procvar
        self.envless_proc_body = procbody
        self.tail = tail

    def lookup(self, var: str) -> DenVal:
        if self.lookupvar == var:
            return ProcVal(self.envless_proc_var, self.envless_proc_body, self)
        else:
            return self.tail.lookup(var)


###################
### Expressions ###
###################
class Expression(ABC):

    @abstractmethod
    def value_of(self, env: Environment) -> ExpVal:
        pass


class ConstExp(Expression):

    def __init__(self, const: int):
        self.const = const

    def value_of(self, env: Environment) -> ExpVal:
        return IntVal(self.const)


class VarExp(Expression):

    def __init__(self, var: str):
        self.var = var

    def value_of(self, env: Environment) -> ExpVal:
        return env.lookup(self.var)


class ProcExp(Expression):

    def __init__(self, var: str, body_exp: Expression):
        self.var = var
        self.body_exp = body_exp

    def value_of(self, env: Environment) -> ExpVal:
        return ProcVal(self.var, self.body_exp, closed_env=env)


class DiffExp(Expression):

    def __init__(self, exp1: Expression, exp2: Expression):
        self.exp1 = exp1
        self.exp2 = exp2

    def value_of(self, env: Environment) -> ExpVal:
        return IntVal(
              IntVal.cast(self.exp1.value_of(env)).value
            - IntVal.cast(self.exp2.value_of(env)).value
        )


class IsZeroExp(Expression):

    def __init__(self, exp: Expression):
        self.exp = exp

    def value_of(self, env: Environment) -> ExpVal:
        return BoolVal(self.exp.value_of(env) == 0)


class IfExp(Expression):

    def __init__(self, cond_exp: Expression, true_exp: Expression, false_exp: Expression):
        self.cond_exp = cond_exp
        self.true_exp = true_exp
        self.false_exp = false_exp

    def value_of(self, env: Environment) -> ExpVal:
        if BoolVal.cast(self.cond_exp.value_of(env)).value:
            return self.true_exp.value_of(env)
        else:
            return self.false_exp.value_of(env)


class LetExp(Expression):

    def __init__(self, var: str, val_exp: Expression, body_exp: Expression):
        self.var = var
        self.val_exp = val_exp
        self.body_exp = body_exp

    def value_of(self, env: Environment) -> ExpVal:
        return self.body_exp.value_of(
            ExtendEnvironment(self.var, self.val_exp.value_of(env), env)
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


class CallExp(Expression):

    def __init__(self, operator_exp: Expression, operand_exp: Expression):
        self.operator = operator_exp
        self.operand = operand_exp

    def value_of(self, env: Environment) -> ExpVal:
        return apply_procedure(ProcVal.cast(self.operator.value_of(env)), self.operand.value_of(env))


def apply_procedure(proc: ProcVal, arg: ExpVal) -> ExpVal:
    return proc.body.value_of(
        ExtendEnvironment(proc.var, arg, proc.closed_env)
    )


class Program:

    def __init__(self, exp: Expression, initenv: Environment):
        self.exp = exp
        self.initenv = initenv

    def value_of_program(self) -> ExpVal:
        return self.exp.value_of(self.initenv)


if __name__ == "__main__":
    prog = Program(
        LetExp("y", ConstExp(74),
               LetExp("p", ProcExp("x", DiffExp(VarExp("y"), VarExp("x"))),
                      CallExp(VarExp("p"), ConstExp(5)))
               ),
        EmptyEnvironment()
    )

    print(IntVal.cast(prog.value_of_program()).value)
