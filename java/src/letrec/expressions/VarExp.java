package letrec.expressions;

import letrec.environments.Environment;
import letrec.values.ExpVal;

public class VarExp extends Expression {

    private final String var;

    public VarExp(String var) {
        this.var = var;
    }

    @Override
    public ExpVal valueOf(Environment env) {
        return env.lookup(var);
    }
}
