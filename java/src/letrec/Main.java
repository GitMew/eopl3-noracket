/**
 * LETREC, Java style.
 * 
 * Author: Thomas Bauwens
 * Date: 2023-01-09
 */
package letrec;

import letrec.environments.EmptyEnvironment;
import letrec.expressions.*;
import letrec.values.*;

public class Main {

    public static void main(String[] args) {
        var program = new LetExp("x", new ConstExp(69), new VarExp("x"));
        var initEnv = new EmptyEnvironment();

        System.out.println(((IntVal)program.valueOf(initEnv)).value);
    }

}
