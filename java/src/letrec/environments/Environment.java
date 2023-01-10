package letrec.environments;

import letrec.values.ExpVal;

public abstract class Environment {

    public abstract ExpVal lookup(String key);

}
