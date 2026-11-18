using System.Text;

if (args.Length != 1)
{
    Console.Error.WriteLine("Usage: Proton.Tools <text-file>");
    return 2;
}

try
{
    var text = await File.ReadAllTextAsync(args[0], Encoding.UTF8);
    if (string.IsNullOrWhiteSpace(text) || text.Trim().Length < 100)
    {
        Console.Error.WriteLine("Corpus must contain at least 100 non-whitespace characters.");
        return 1;
    }

    Console.WriteLine($"Corpus OK: {text.Length} characters, {text.Split((char[]?)null, StringSplitOptions.RemoveEmptyEntries).Length} words");
    return 0;
}
catch (Exception ex) when (ex is IOException or UnauthorizedAccessException)
{
    Console.Error.WriteLine(ex.Message);
    return 1;
}
