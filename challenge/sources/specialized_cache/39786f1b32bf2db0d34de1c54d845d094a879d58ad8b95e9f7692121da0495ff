import java.util.Random;

public class Main {
    public static void main(String[] args) {
        long[] rng_opts = {1699724873L, 2804711513L, 720410643L, 3739283460L, 2577785431L, 1607299265L};

        for (int i = 0; i < rng_opts.length; i++) {
            // our Java function accepts ints as parameters so we have to take the float values and conv to int
            Random tmprng = new Random((int)(rng_opts[i] & 0xFFFFFFFFL));
            System.out.print(tmprng.nextInt() & 0xFFFFFFFFL);
            System.out.print(", ");
        }
    }
}

// javac Main.java && java Main