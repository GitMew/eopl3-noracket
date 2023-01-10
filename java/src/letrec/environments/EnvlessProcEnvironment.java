package letrec.environments;

import letrec.expressions.Expression;
import letrec.values.ExpVal;
import letrec.values.ProcVal;

public class EnvlessProcEnvironment extends Environment {

    private final String procName;
    private final String procVar;
    private final Expression procBody;
    private final Environment tail;

    public EnvlessProcEnvironment(String procName, String procVar, Expression procBody, Environment tail) {
        this.procName = procName;
        this.procVar = procVar;
        this.procBody = procBody;
        this.tail = tail;
    }

    @Override
    public ExpVal lookup(String key) {
        if (key.equals(procName)) {
            return new ProcVal(procVar, procBody, this);
        } else {
            return tail.lookup(key);
        }
    }
}
