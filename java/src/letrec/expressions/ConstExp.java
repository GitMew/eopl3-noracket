package letrec.expressions;

import letrec.environments.Environment;
import letrec.values.ExpVal;
import letrec.values.IntVal;

public class ConstExp extends Expression {

    private final int value;

    public ConstExp(int value) {
        this.value = value;
    }

    @Override
    public ExpVal valueOf(Environment env) {
        return new IntVal(value);
    }
}
