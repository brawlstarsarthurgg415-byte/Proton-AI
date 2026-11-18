#!/usr/bin/env ruby
# Reports basic corpus statistics. It does not certify factual quality or licensing.
path = ARGV.fetch(0) { abort "usage: ruby corpus_report.rb <text-file>" }
text = File.read(path, encoding: "UTF-8")
abort "Corpus is empty" if text.strip.empty?

words = text.scan(/[[:alnum:]_]+/u)
unique = words.map(&:downcase).uniq
puts "Characters: #{text.length}"
puts "Words: #{words.length}"
puts "Unique words: #{unique.length}"
puts "Approximate repetition ratio: #{words.empty? ? 0 : (1.0 - unique.length.to_f / words.length).round(3)}"
