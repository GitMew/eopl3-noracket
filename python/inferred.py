"""
INFERRED interpreter.

TODO: Although Python allows us to be messy at runtime, statically all the .type_of calls below are illegal.
      Is there a solution that doesn't involve copying __init__ and value_of from IMPLICIT-REFS?

Author: Thomas Bauwens
Date: 2023-01-25
"""
from implicit_refs import *

# PART 1: Unification

# Types
class Typish:
    pass

class UnknownType(Typish):
    pass

class Type(Typish, ABC):

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

        You also need it as the first call to apply any existing substitutions, obviously.
        """
        lhs = substitution.applyThisToType(self)
        rhs = substitution.applyThisToType(other)
        lhs._unify(rhs, substitution)


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

class IntBaseType(BaseType):
    def __init__(self):
        super().__init__("int")

class BoolBaseType(BaseType):
    def __init__(self):
        super().__init__("bool")

class ForEffectType(IntBaseType):
    """
    Expressions that are "for effect" have a return value that shouldn't be used (e.g. SetRef and Set).
    This is chosen to be a NumVal, so the type is an int.
    """
    pass


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


# PART 2: type_of expressions (note: the entire Martelli-Montanari algorithm, i.e. unification, has already been implemented above!)
class TypePurifier:

    def __init__(self):
        self.current_id = 0

    def toType(self, typish: Typish) -> Type:
        if not isinstance(typish, UnknownType):
            return typish

        self.current_id += 1
        return TypeVariable(self.current_id)


THE_PURIFIER = TypePurifier()

####################
### Environments ###
####################
class TypedEnvironment:

    @abstractmethod
    def lookup(self, var: str) -> Type:
        pass

    @abstractmethod
    def replace(self, var: str, new_type: Type):
        """
        To support IMPLICIT-REFS without tracking a whole type store, we allow replacing the topmost occurrence of
        a variable by a different type. This works because the SetExp has access to only this occurrence too.
        This cannot support EXPLICIT-REFS, so for that, you'll need to introduce more type annotations, or a type store.
        """
        pass

class EmptyEnvironmentTyped(TypedEnvironment):

    def lookup(self, var: str) -> Type:
        raise ValueError(f"Failed to find type for variable '{var}'.")

    def replace(self, var: str, new_type: Type):
        raise ValueError(f"Failed to find variable to replace '{var}'.")

class ExtendEnvironmentTyped(TypedEnvironment):

    def __init__(self, var: str, val: Type, tail: TypedEnvironment):
        self.var = var
        self.val = val
        self.tail = tail

    def lookup(self, var: str) -> Type:
        if var == self.var:
            return self.val
        else:
            return self.tail.lookup(var)

    def replace(self, var: str, new_type: Type):
        if var == self.var:
            self.val = new_type
        else:
            self.tail.replace(var, new_type)


###################
### Expressions ###
###################
class TypedExpression(Expression):

    @abstractmethod
    def type_of(self, env: TypedEnvironment, sub: Substitution) -> Type:
        pass


class ConstExpTyped(TypedExpression, ConstExp):

    def type_of(self, env: TypedEnvironment, sub: Substitution) -> Type:
        return IntBaseType()


class VarExpTyped(TypedExpression, VarExp):

    def type_of(self, env: TypedEnvironment, sub: Substitution) -> Type:
        return env.lookup(self.var)


class DiffExpTyped(TypedExpression, DiffExp):

    def type_of(self, env: TypedEnvironment, sub: Substitution) -> Type:
        type1: Type = self.exp1.type_of(env, sub)  # FIXME: Works at runtime, not statically.
        type1.unify(IntBaseType(), sub)  # Type equation 1: t_e1 = int
        type2: Type = self.exp2.type_of(env, sub)
        type2.unify(IntBaseType(), sub)  # Type equation 2: t_e2 = int
        return IntBaseType()             # Type equation 3: t_res = int


class IsZeroExpTyped(TypedExpression, IsZeroExp):

    def type_of(self, env: TypedEnvironment, sub: Substitution) -> Type:
        type: Type = self.exp.type_of(env, sub)
        type.unify(IntBaseType(), sub)  # Type equation 1: t_exp = int
        return BoolBaseType()           # Type equation 2: t_res = bool


class IfExpTyped(TypedExpression, IfExp):

    def type_of(self, env: TypedEnvironment, sub: Substitution) -> Type:
        type_cond: Type = self.cond_exp.type_of(env, sub)
        type_cond.unify(BoolBaseType(), sub)  # Type equation 1: t_cond = bool
        type_res1: Type = self.true_exp.type_of(env, sub)
        type_res2: Type = self.false_exp.type_of(env, sub)
        type_res1.unify(type_res2, sub)         # Type equation 2: t_branch1 = t_branch2
        return type_res1                        # Type equation 3 t_res = t_branch1


class LetExpTyped(TypedExpression, LetExp):

    def type_of(self, env: TypedEnvironment, sub: Substitution) -> Type:
        type_val: Type = self.val_exp.type_of(env, sub)
        return self.body_exp.type_of(ExtendEnvironmentTyped(self.var, type_val, env), sub)


class CallExpTyped(TypedExpression, CallExp):

    def type_of(self, env: TypedEnvironment, sub: Substitution) -> Type:
        res_type: Type = THE_PURIFIER.toType(UnknownType())
        proc_type: Type = self.operator.type_of(env, sub)
        arg_type: Type  = self.operand.type_of(env, sub)
        proc_type.unify(ProcType(arg_type, res_type), sub)  # Type equation 1: proc_type = arg_type -> res_type
        return res_type


class SetExpTyped(TypedExpression, SetExp):

    def type_of(self, env: TypedEnvironment, sub: Substitution) -> Type:
        val_type: Type = self.value_exp.type_of(env, sub)
        env.replace(self.var, val_type)
        return ForEffectType()


# These last two expressions have a new constructor due to type annotations
class LetrecExpTyped(TypedExpression, LetrecExp):

    def __init__(self, procname: str, procvar: str, procbody: Expression, letbody: Expression,
                 return_type: Typish, var_type: Typish):
        super().__init__(procname, procvar, procbody, letbody)
        self.tr = return_type
        self.tv = var_type

    def type_of(self, env: TypedEnvironment, sub: Substitution) -> Type:
        arg_type = THE_PURIFIER.toType(self.tv)
        ret_type = THE_PURIFIER.toType(self.tr)
        proc_type = ProcType(arg_type, ret_type)
        env_with_proc = ExtendEnvironmentTyped(self.procname, proc_type, env)
        # The proc body can look up both the recursive proc AND its variable.
        procbody_type: Type = self.procbody.type_of(ExtendEnvironmentTyped(self.procvar, arg_type, env_with_proc), sub)
        procbody_type.unify(ret_type, sub)                # Type equation 1: t_procbody = t_procreturn
        # The let body only knows about the proc
        return self.letbody.type_of(env_with_proc, sub)  # Type equation 2: t_letrec = t_letbody


class ProcExpTyped(TypedExpression, ProcExp):

    def __init__(self, var: str, body_exp: Expression,
                 var_type: Typish):
        super().__init__(var, body_exp)
        self.tv = var_type

    def type_of(self, env: TypedEnvironment, sub: Substitution) -> Type:
        arg_type = THE_PURIFIER.toType(self.tv)
        return_type: Type = self.body_exp.type_of(ExtendEnvironmentTyped(self.var, arg_type, env), sub)
        return ProcType(arg_type, return_type)  # There's no need for a unification because the only equation is the result equation. If self.tv is a type variable, then its substitution will be in sub if it was resolved in the body.
