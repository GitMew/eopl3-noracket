package letrec.expressions;

import letrec.environments.Environment;
import letrec.environments.ExtendEnvironment;
import letrec.values.ExpVal;

public class LetExp extends Expression {

    private final String var;
    private final Expression valExp;
    private final Expression bodyExp;

    public LetExp(String var, Expression valExp, Expression bodyExp) {
        this.var = var;
        this.valExp = valExp;
        this.bodyExp = bodyExp;
    }


    @Override
    public ExpVal valueOf(Environment env) {
        return bodyExp.valueOf(
            new ExtendEnvironment(var, valExp.valueOf(env), env)
        );
    }
}
