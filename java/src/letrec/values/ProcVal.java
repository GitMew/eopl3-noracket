package letrec.values;

import letrec.environments.Environment;
import letrec.expressions.Expression;

public class ProcVal extends ExpVal {

    public final String var;
    public final Expression body;
    public final Environment closedEnv;

    public ProcVal(String var, Expression body, Environment closedEnv) {
        this.var = var;
        this.body = body;
        this.closedEnv = closedEnv;
    }
}
