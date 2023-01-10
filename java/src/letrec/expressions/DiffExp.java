package letrec.expressions;

import letrec.environments.Environment;
import letrec.values.ExpVal;
import letrec.values.IntVal;

public class DiffExp extends Expression {

    private final Expression exp1;
    private final Expression exp2;

    public DiffExp(Expression exp1, Expression exp2) {
        this.exp1 = exp1;
        this.exp2 = exp2;
    }

    @Override
    public ExpVal valueOf(Environment env) {
        return new IntVal(
            ((IntVal)exp1.valueOf(env)).value - ((IntVal)exp2.valueOf(env)).value
        );
    }
}
