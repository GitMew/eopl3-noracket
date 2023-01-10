package letrec.environments;

import letrec.values.ExpVal;

public class EmptyEnvironment extends Environment {

    @Override
    public ExpVal lookup(String key) {
        throw new ArrayIndexOutOfBoundsException("Failed to find key " + key + " in environment.");
//        return null;
    }
}
