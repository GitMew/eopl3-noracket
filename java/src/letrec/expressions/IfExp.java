package letrec.expressions;

import letrec.environments.Environment;
import letrec.values.BoolVal;
import letrec.values.ExpVal;

public class IfExp extends Expression {

    private final Expression condExp;
    private final Expression trueExp;
    private final Expression falseExp;

    public IfExp(Expression condExp, Expression trueExp, Expression falseExp) {
        this.condExp = condExp;
        this.trueExp = trueExp;
        this.falseExp = falseExp;
    }

    @Override
    public ExpVal valueOf(Environment env) {
        if (((BoolVal)condExp.valueOf(env)).value) {
            return trueExp.valueOf(env);
        } else {
            return falseExp.valueOf(env);
        }
    }
}
