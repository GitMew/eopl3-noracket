"""
INFERRED interpreter.

TODO: type_of. The unification has been implemented, though.

Author: Thomas Bauwens
Date: 2023-01-25
"""
from implicit_refs import *


# Types
class Type(ABC):

    @abstractmethod
    def _unify(self, other: "Type", substitution: "Substitution"):
        """
        Given a type equation "self = other", add all consequent rules to the given substitution.
        Assumes the given substitution has already been applied to self and other.
        """
        pass

    @abstractmethod
    def applyRuleToThis(self, rule: "Rule") -> "Type":
        """
        Given a rule "TYPEVAR -> TYPE", find all occurrences of TYPEVAR and replace it by TYPE in this type.
        """
        pass

    @abstractmethod
    def contains(self, tvar: "TypeVariable") -> bool:
        """
        Whether the type contains the given type variable.
        """
        pass

    def unify(self, other: "Type", substitution: "Substitution"):
        """
        Applies the given substitution to self and other before calling _unify().

        This is needed in recursive implementations of _unify(). Take as example
            t1 -> (int -> t1) = bool -> (t3 -> t4)
        When unified, t1 = bool is found first, which means the remaining unification is now not
            int -> t1 = t3 -> t4
        but, with the newest rule applied,
            int -> bool = t3 -> t4
        which is solvable.

        You also need it as the top call from outside
        """
        lhs = substitution.applyThisToType(self)
        rhs = substitution.applyThisToType(other)
        lhs._unify(rhs, substitution)


class UnknownType(Type):
    pass


class TypeVariable(Type):

    def __init__(self, num: int):
        self.num = num

    def _unify(self, other: "Type", substitution: "Substitution"):
        if isinstance(other, TypeVariable):  # tv1 = tv2
            if self.num != other.num:
                substitution.append(Rule(self, other))
        elif other.contains(self):  # tv1 = T(tv1)
            raise TypeError("Circular error detected.")
        else:
            substitution.append(Rule(self, other))

    def applyRuleToThis(self, rule: "Rule") -> "Type":
        if self.num == rule.head.num:
            return rule.body
        else:
            return self

    def contains(self, tvar: "TypeVariable") -> bool:
        return self.num == tvar.num


class BaseType(Type):

    def __init__(self, typename: str):
        self.name = typename

    def applyRuleToThis(self, rule: "Rule") -> "Type":
        return self

    def _unify(self, other: "Type", substitution: "Substitution"):
        if isinstance(other, BaseType) and self.name == other.name:  # int = int
            pass
        elif isinstance(other, TypeVariable):  # int = tv1
            other.unify(self, substitution)
        else:
            raise TypeError("Conflicting equation found.")

    def contains(self, tvar: "TypeVariable") -> bool:
        return False


class ProcType(Type):

    def __init__(self, t1: Type, t2: Type):
        self.t1 = t1
        self.t2 = t2

    def applyRuleToThis(self, rule: "Rule") -> "Type":
        return ProcType(self.t1.applyRuleToThis(rule), self.t2.applyRuleToThis(rule))

    def _unify(self, other: "Type", substitution: "Substitution"):
        if isinstance(other, ProcType):
            self.t1.unify(other.t1, substitution)
            self.t2.unify(other.t2, substitution)
        else:
            raise TypeError("Conflicting equation found.")

    def contains(self, tvar: "TypeVariable") -> bool:
        return self.t1.contains(tvar) or self.t2.contains(tvar)


# Substitution
class Rule:

    def __init__(self, head: TypeVariable, body: Type):
        self.head = head
        self.body = body


class Substitution:

    def __init__(self):
        self.rules = []

    def applyThisToType(self, old_type: Type) -> Type:
        for rule in self.rules:
            old_type = old_type.applyRuleToThis(rule)
        return old_type

    def append(self, new_rule: Rule):
        for r in self.rules:
            r.body = r.body.applyRuleToThis(new_rule)
        self.rules.append(new_rule)


# Expressions
class LetrecExpTyped(LetrecExp):

    def __init__(self, procname: str, procvar: str, procbody: Expression, letbody: Expression,
                 return_type: Type, var_type: Type):
        super().__init__(procname, procvar, procbody, letbody)
        self.tr = return_type
        self.tv = var_type


class ProcExpTyped(ProcExp):

    def __init__(self, var: str, body_exp: Expression,
                 var_type: Type):
        super().__init__(var, body_exp)
        self.tv = var_type

