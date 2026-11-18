package ai.proton.text;

import java.text.Normalizer;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

/** Unicode-aware corpus utilities. This is a word tokenizer, not a neural tokenizer. */
public final class Tokenizer {
    private Tokenizer() {}

    public static List<String> tokenize(String input) {
        String normalized = Normalizer.normalize(input, Normalizer.Form.NFKC)
                .toLowerCase(Locale.ROOT);
        List<String> result = new ArrayList<>();
        for (String token : normalized.split("[^\\p{L}\\p{N}_]+")) {
            if (!token.isBlank()) result.add(token);
        }
        return List.copyOf(result);
    }

    public static Map<String, Integer> frequencies(String input) {
        Map<String, Integer> counts = new LinkedHashMap<>();
        for (String token : tokenize(input)) counts.merge(token, 1, Integer::sum);
        return Map.copyOf(counts);
    }

    public static double repetitionRatio(String input) {
        List<String> tokens = tokenize(input);
        if (tokens.isEmpty()) return 0.0;
        return 1.0 - (double) frequencies(input).size() / tokens.size();
    }

    public static List<Map.Entry<String, Integer>> mostFrequent(String input, int limit) {
        if (limit < 0) throw new IllegalArgumentException("limit cannot be negative");
        return frequencies(input).entrySet().stream()
                .sorted(Map.Entry.<String, Integer>comparingByValue(Comparator.reverseOrder())
                        .thenComparing(Map.Entry.comparingByKey()))
                .limit(limit)
                .toList();
    }

    public static String normalizeForComparison(String input) {
        return Normalizer.normalize(input, Normalizer.Form.NFKC)
                .toLowerCase(Locale.ROOT).strip().replaceAll("\\s+", " ");
    }

    public static void main(String[] args) {
        if (args.length == 0) {
            System.out.println("Usage: java ai.proton.text.Tokenizer <text>");
            return;
        }
        String input = String.join(" ", args);
        List<String> tokens = tokenize(input);
        System.out.println("Tokens: " + tokens.size());
        System.out.println("Unique: " + frequencies(input).size());
        System.out.printf(Locale.ROOT, "Repetition: %.3f%n", repetitionRatio(input));
        System.out.println(String.join("\n", tokens));
    }
}
