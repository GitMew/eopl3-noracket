package letrec.environments;

import letrec.values.ExpVal;

public class ExtendEnvironment extends Environment {

    private final String var;
    private final ExpVal val;
    private final Environment tail;

    public ExtendEnvironment(String var, ExpVal value, Environment tail) {
        this.var = var;
        this.val = value;
        this.tail = tail;
    }

    @Override
    public ExpVal lookup(String key) {
        if (key.equals(var)) {
            return val;
        } else {
            return tail.lookup(key);
        }
    }
}
