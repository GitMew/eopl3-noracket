package letrec.expressions;

import letrec.environments.Environment;
import letrec.values.ExpVal;
import letrec.values.ProcVal;

public class ProcExp extends Expression {

    private final String var;
    private final Expression body;

    public ProcExp(String var, Expression body) {
        this.var = var;
        this.body = body;
    }

    @Override
    public ExpVal valueOf(Environment env) {
        return new ProcVal(var, body, env);
    }
}
