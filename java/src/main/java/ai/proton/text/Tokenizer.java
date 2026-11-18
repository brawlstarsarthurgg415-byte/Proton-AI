package ai.proton.text;

import java.text.Normalizer;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

/** Basic Unicode-aware word splitter; not a neural tokenizer. */
public final class Tokenizer {
    private Tokenizer() {}

    public static List<String> tokenize(String input) {
        String normalized = Normalizer.normalize(input, Normalizer.Form.NFKC)
                .toLowerCase(Locale.ROOT);
        List<String> result = new ArrayList<>();
        for (String token : normalized.split("[^\\p{L}\\p{N}_]+")) {
            if (!token.isBlank()) result.add(token);
        }
        return result;
    }

    public static void main(String[] args) {
        if (args.length == 0) {
            System.out.println("Usage: java ai.proton.text.Tokenizer <text>");
            return;
        }
        System.out.println(String.join("\n", tokenize(String.join(" ", args))));
    }
}
