#!/usr/bin/env ruby
# Audits a UTF-8 corpus without changing the source file.
require "json"
require "optparse"

class CorpusReport
  attr_reader :text

  def initialize(text)
    raise ArgumentError, "input is not valid UTF-8" unless text.valid_encoding?
    @text = text.encode("UTF-8")
    raise ArgumentError, "corpus is empty" if @text.strip.empty?
  end

  def words
    @text.downcase.scan(/[[:alnum:]_]+/u)
  end

  def frequencies
    words.tally
  end

  def repetition_ratio
    tokens = words
    return 0.0 if tokens.empty?
    1.0 - frequencies.length.to_f / tokens.length
  end

  def report(path = nil)
    tokens = words
    {
      file: path,
      bytes: @text.bytesize,
      characters: @text.length,
      lines: @text.lines.count,
      words: tokens.length,
      unique_words: frequencies.length,
      repeated_words: tokens.length - frequencies.length,
      repetition_ratio: repetition_ratio.round(4),
      top_words: frequencies.sort_by { |word, count| [-count, word] }.first(10).to_h
    }
  end
end

options = { json: false, min_words: 1 }
OptionParser.new do |parser|
  parser.banner = "Usage: ruby corpus_report.rb [--json] [--min-words N] <text-file>"
  parser.on("--json", "print JSON") { options[:json] = true }
  parser.on("--min-words N", Integer, "minimum token count") { |n| options[:min_words] = n }
end.parse!

path = ARGV.shift or abort "Usage: ruby corpus_report.rb [--json] [--min-words N] <text-file>"
begin
  result = CorpusReport.new(File.read(path, encoding: "UTF-8"))
  data = result.report(path)
  abort "Corpus has too few words" if data[:words] < options[:min_words]
  puts(options[:json] ? JSON.pretty_generate(data) : data.map { |key, value| "#{key}: #{value}" }.join("\n"))
rescue SystemCallError, ArgumentError => error
  warn "Corpus error: #{error.message}"
  exit 1
end
