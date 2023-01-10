"""
EXPLICIT-REFS, which is LETREC plus pointer memory.

Author: Thomas Bauwens
Date: 2023-01-06
"""
from letrec import *
from typing import List


##############################
### Extra expressed values ###
##############################
class Reference(ExpVal):

    def __init__(self, address: int):
        self.value = address


#########################
### Extra expressions ###
#########################
class BeginExp(Expression):

    def __init__(self, subexpressions: List[Expression]):
        self.exps = subexpressions

    def value_of(self, env: Environment) -> ExpVal:
        result = IntVal(-1_000_000)
        for exp in self.exps:
            result = exp.value_of(env)
        return result


class NewrefExp(Expression):

    def __init__(self, init_exp: Expression):
        self.init_exp = init_exp

    def value_of(self, env: Environment) -> ExpVal:
        return THE_STORE.store(THE_STORE.new(), self.init_exp.value_of(env))


class SetrefExp(Expression):

    def __init__(self, ref_exp: Expression, val_exp: Expression):
        self.ref_exp = ref_exp
        self.val_exp = val_exp

    def value_of(self, env: Environment) -> ExpVal:
        THE_STORE.store(Reference.cast(self.ref_exp.value_of(env)), self.val_exp.value_of(env))
        return IntVal(-1_000_001)


class DerefExp(Expression):

    def __init__(self, ref_exp: Expression):
        self.ref_exp = ref_exp

    def value_of(self, env: Environment) -> ExpVal:
        return THE_STORE.load(Reference.cast(self.ref_exp.value_of(env)))


#################
### The Store ###
#################
class Store:

    def __init__(self):
        self.cursor = 0
        self.values = []

    def load(self, address: Reference) -> ExpVal:
        return self.values[address.value]

    def store(self, address: Reference, value: ExpVal) -> Reference:
        """
        The Store stores expressed values, not denoted values. This is most obvious in IMPLICIT-REFS.
        The returned reference is just the given address; makes a lot of code shorter.
        """
        self.values[address.value] = value
        return address

    def new(self) -> Reference:
        pointer = self.cursor
        self.values.append(IntVal(-1_000_004))
        self.cursor += 1
        return Reference(pointer)

    def __repr__(self):
        r = "["
        for i,v in enumerate(self.values):
            r += "\t" + str(i) + " " + v.__repr__() + "\n"
        r += "]"
        return r


THE_STORE = Store()
