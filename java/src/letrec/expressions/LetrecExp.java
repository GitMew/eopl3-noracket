package letrec.expressions;

import letrec.environments.Environment;
import letrec.environments.EnvlessProcEnvironment;
import letrec.values.ExpVal;

public class LetrecExp extends Expression {

    private final String procName;
    private final String procVar;
    private final Expression procBody;
    private final Expression bodyExp;

    public LetrecExp(String procName, String procVar, Expression procBody, Expression bodyExp) {
        this.procName = procName;
        this.procVar = procVar;
        this.procBody = procBody;
        this.bodyExp = bodyExp;
    }

    @Override
    public ExpVal valueOf(Environment env) {
        return bodyExp.valueOf(
                new EnvlessProcEnvironment(procName, procVar, procBody, env)
        );
    }
}
