using System.Text;
using System.Text.Json;

internal sealed record CorpusReport(
    string File,
    int Bytes,
    int Characters,
    int Lines,
    int Words,
    int UniqueWords,
    int RepeatedWords,
    double RepetitionRatio,
    IReadOnlyList<KeyValuePair<string, int>> MostFrequent);

internal static class CorpusAnalyzer
{
    public static CorpusReport Analyze(string path, string text)
    {
        if (string.IsNullOrWhiteSpace(text))
            throw new ArgumentException("Corpus is empty.");
        var words = text.ToLowerInvariant()
            .Split((char[]?)null, StringSplitOptions.RemoveEmptyEntries);
        var frequencies = words.GroupBy(word => word)
            .ToDictionary(group => group.Key, group => group.Count());
        var ordered = frequencies.OrderByDescending(pair => pair.Value)
            .ThenBy(pair => pair.Key, StringComparer.Ordinal)
            .Take(10).ToArray();
        var unique = frequencies.Count;
        return new CorpusReport(
            Path.GetFileName(path),
            Encoding.UTF8.GetByteCount(text),
            text.EnumerateRunes().Count(),
            text.Replace("\r\n", "\n").Split('\n').Length,
            words.Length,
            unique,
            words.Length - unique,
            words.Length == 0 ? 0 : 1.0 - (double)unique / words.Length,
            ordered);
    }
}

static class Program
{
    static async Task<int> Main(string[] args)
    {
        var json = args.Contains("--json");
        var positional = args.Where(arg => arg != "--json").ToArray();
        if (positional.Length != 1)
        {
            Console.Error.WriteLine("Usage: Proton.Tools [--json] <text-file>");
            return 2;
        }

        try
        {
            var text = await File.ReadAllTextAsync(positional[0], Encoding.UTF8);
            var report = CorpusAnalyzer.Analyze(positional[0], text);
            if (json)
                Console.WriteLine(JsonSerializer.Serialize(report, new JsonSerializerOptions { WriteIndented = true }));
            else
                Console.WriteLine($"Corpus OK: {report.Bytes} bytes, {report.Characters} characters, {report.Words} words, repetition {report.RepetitionRatio:P1}");
            return 0;
        }
        catch (Exception error) when (error is IOException or UnauthorizedAccessException or ArgumentException)
        {
            Console.Error.WriteLine($"Corpus error: {error.Message}");
            return 1;
        }
    }
}
