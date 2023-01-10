package letrec.expressions;

import letrec.environments.Environment;
import letrec.values.ExpVal;

public abstract class Expression {

    public abstract ExpVal valueOf(Environment env);

}
