
// --- TYPES ---
type Identifier = Box<str>;  // "String" is mutable, "str" has no predefined size, and "&str" needs a lifetime. So, Box<str> it is.

pub enum Expression {
    
    ConstExp { num: i32 },
    
    VarExp { var: Identifier },
    
    DiffExp {
        exp1: Box<Expression>,
        exp2: Box<Expression>
    },
    
    ZeroTestExp { exp: Box<Expression> },
    
    IfExp {
        condExp: Box<Expression>,
        trueExp: Box<Expression>,
        falseExp: Box<Expression>
    },
    
    LetExp {
        var: Identifier,
        valExp: Box<Expression>,
        bodyExp: Box<Expression>
    },
    
    ProcExp {
        var: Identifier,
        body: Box<Expression>
    },

    CallExp {
        operator: Box<Expression>,
        operand: Box<Expression>
    },

    LetrecExp {
        name: Identifier,
        var: Identifier,
        procbody: Box<Expression>,
        letbody: Box<Expression>
    }
}

pub enum Environment {
    EmptyEnvironment,
    ExtendEnvironment { var: Identifier, val: ExpVal, tail: Box<Environment> },
    ExtendRecEnvironment { name: Identifier, var: Identifier, body: Expression, tail: Box<Environment> }
}

enum ProcType {
    Procedure { var: Identifier, body: Expression, closure: Box<Environment> }  // Doesn't need to put Expression in a box, because these two are part of different systems (syntax vs. semantics).
}

enum ExpVal {
    NumVal { val: i32 },
    BoolVal { val: bool },
    ProcVal { val: ProcType }
}

type DenVal = ExpVal;


// --- TRAITS ---

trait Lookup {
    fn lookup(&self, key: &Identifier) -> Result<&DenVal, &str>;  // The key is a borrow because the intention is not that lookup takes ownership of it.
}

impl Lookup for Environment {
    fn lookup(&self, key: &Identifier) -> Result<&DenVal, &str> {
        match self {
            Environment::EmptyEnvironment => Err("Lookup failed."),
            Environment::ExtendEnvironment { var, val, tail } =>
                if *var == *key {
                    Ok(val)
                } else {
                    tail.lookup(key)
                }
            Environment::ExtendRecEnvironment { name, var, body, tail } => 
                if *name == *key {
                    Ok(&ExpVal::ProcVal { val: ProcType::Procedure { var: *var, body: *body, closure: Box::new(*self) } })
                } else {
                    tail.lookup(key)
                },
        }
    }
}

trait Unpack {
    fn toNum(&self) -> Result<i32, &str>;
    fn toBool(&self) -> Result<bool, &str>;
    fn toProc(&self) -> Result<&ProcType, &str>;  // Since &self is an immutable borrow, the field we want to extract is only accessible as an immutable borrow too.
}

impl Unpack for ExpVal {
    fn toNum(&self) -> Result<i32, &str> {
        match self {
            ExpVal::NumVal { val } => Ok(*val),
            _ => Err("Failed to convert to number.")
        }
    }

    fn toBool(&self) -> Result<bool, &str> {
        match self {
            ExpVal::BoolVal { val } => Ok(*val),
            _ => Err("Failed to convert to boolean.")
        }
    }

    fn toProc(&self) -> Result<&ProcType, &str> {
        match self {
            ExpVal::ProcVal { val } => Ok(val),
            _ => Err("Failed to convert to procedure.")
        }
    }
}

trait Semantics {
    fn valueOf(&self, env: &Environment) -> Result<ExpVal, &str>;  // Cannot alter the env; only make a new extended env with it.
}

impl Semantics for Expression {
    fn valueOf(&self, env: &Environment) -> Result<ExpVal, &str> {
        match self {
            Expression::ConstExp { num } => 
                Ok(ExpVal::NumVal { val: *num }),
            Expression::VarExp { var } => 
                match env.lookup(var) {
                    Ok(denval) => Ok(denval),  // FIXME: Probably need a Copy trait on ExpVal, but ooooffff. 
                    //Ok(denval) => Ok(ExpVal::NumVal { val: 0 }),
                    Err(msg) => Err(msg),
                },
            Expression::DiffExp { exp1, exp2 } => 
                match exp1.valueOf(env) {
                    Ok(val1) => match val1.toNum() {
                        Ok(val1) => match exp2.valueOf(env) {
                            Ok(val2) => match val2.toNum() {
                                Ok(val2) => Ok(ExpVal::NumVal { val: val1 - val2 }),
                                Err(msg) => Err(msg)
                            },
                            Err(msg) => Err(msg)
                        },
                        Err(msg) => Err(msg)
                    }                    
                    Err(msg) => Err(msg)
                },
            Expression::ZeroTestExp { exp } => 
                match exp.valueOf(env) {
                    Ok(val) => match val.toNum() {
                        Ok(val) => if val == 0 { 
                            Ok(ExpVal::BoolVal { val: true }) 
                        } else { 
                            Ok(ExpVal::BoolVal { val: false }) 
                        },
                        Err(msg) => Err(msg)
                    }
                    Err(msg) => Err(msg)
                },
            Expression::IfExp { condExp, trueExp, falseExp } => 
                match condExp.valueOf(env) {
                    Ok(condVal) => match condVal.toBool() {
                        Ok(val) => if val { trueExp.valueOf(env) } else { falseExp.valueOf(env) },
                        Err(msg) => Err(msg)
                    },
                    Err(msg) => Err(msg)
                },
            Expression::LetExp { var, valExp, bodyExp } =>
                match valExp.valueOf(env) {
                    Ok(val) => 
                        bodyExp.valueOf(&Environment::ExtendEnvironment { var: *var, val: val, tail: Box::new(*env) }),
                    Err(msg) => Err(msg)
                },
            Expression::ProcExp { var, body } =>
                Ok(ExpVal::ProcVal { val: ProcType::Procedure { var: *var, body: **body, closure: Box::new(*env) } } ),
            Expression::CallExp { operator, operand } =>
                match operator.valueOf(env) {
                    Ok(rator) => match rator.toProc() {
                        Ok(rator) => match operand.valueOf(env) {
                            Ok(rand) => match rator { ProcType::Procedure { var, body, closure } =>
                                body.valueOf(&Environment::ExtendEnvironment { var: *var, val: rand, tail: Box::new(*env) } )
                            },
                            Err(msg) => Err(msg)
                        },
                        Err(msg) => Err(msg)
                    }                    
                    Err(msg) => Err(msg)
                },
            Expression::LetrecExp { name, var, procbody, letbody } => 
                letbody.valueOf(&Environment::ExtendRecEnvironment { name: *name, var: *var, body: **procbody, tail: Box::new(*env) }),
        }
    }
}
