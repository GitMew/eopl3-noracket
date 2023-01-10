package letrec.expressions;

import letrec.environments.*;
import letrec.values.*;

public class CallExp extends Expression {

    private final Expression operatorExp;
    private final Expression operandExp;

    public CallExp(Expression operatorExp, Expression operandExp) {
        this.operatorExp = operatorExp;
        this.operandExp = operandExp;
    }

    @Override
    public ExpVal valueOf(Environment env) {
        return applyProcedure((ProcVal)operatorExp.valueOf(env), operandExp.valueOf(env));
    }

    public static ExpVal applyProcedure(ProcVal proc, ExpVal arg) {
        return proc.body.valueOf(
                new ExtendEnvironment(proc.var, arg, proc.closedEnv)
        );
    }
}
