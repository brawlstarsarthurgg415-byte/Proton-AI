package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"strings"
	"unicode/utf8"
)

type Report struct {
	File       string         `json:"file"`
	Bytes      int            `json:"bytes"`
	Characters int            `json:"characters"`
	Lines      int            `json:"lines"`
	Words      int            `json:"words"`
	Unique     int            `json:"unique_words"`
	Repeated   int            `json:"repeated_words"`
	Subjects   map[string]int `json:"subject_counts,omitempty"`
}

func Analyze(name string, data []byte) (Report, error) {
	if !utf8.Valid(data) { return Report{}, fmt.Errorf("file is not valid UTF-8") }
	text := strings.TrimSpace(string(data))
	if text == "" { return Report{}, fmt.Errorf("corpus is empty") }
	words := strings.FieldsFunc(strings.ToLower(text), func(r rune) bool {
		return !(r == '_' || r >= 'a' && r <= 'z' || r >= '0' && r <= '9' || r > 127)
	})
	frequencies := make(map[string]int)
	for _, word := range words { frequencies[word]++ }
	repeated := 0
	for _, count := range frequencies { if count > 1 { repeated += count - 1 } }
	lines := strings.Split(strings.ReplaceAll(text, "\r\n", "\n"), "\n")
	return Report{File:name, Bytes:len(data), Characters:utf8.RuneCount(data), Lines:len(lines), Words:len(words), Unique:len(frequencies), Repeated:repeated}, nil
}

func main() {
	jsonOutput := flag.Bool("json", false, "write machine-readable JSON")
	minWords := flag.Int("min-words", 1, "minimum number of words required")
	flag.Parse()
	if flag.NArg() != 1 { fmt.Fprintln(os.Stderr, "usage: corpuscheck [--json] [--min-words N] <text-file>"); os.Exit(2) }
	path := flag.Arg(0)
	data, err := os.ReadFile(path)
	if err != nil { fmt.Fprintln(os.Stderr, err); os.Exit(1) }
	report, err := Analyze(path, data)
	if err == nil && report.Words < *minWords { err = fmt.Errorf("corpus has %d words; minimum is %d", report.Words, *minWords) }
	if err != nil { fmt.Fprintln(os.Stderr, "invalid corpus:", err); os.Exit(1) }
	if *jsonOutput { enc:=json.NewEncoder(os.Stdout); enc.SetIndent("", "  "); if err:=enc.Encode(report); err!=nil { fmt.Fprintln(os.Stderr,err); os.Exit(1) }; return }
	fmt.Printf("Corpus OK: %d bytes, %d characters, %d lines, %d words (%d unique, %d repeated)\n", report.Bytes, report.Characters, report.Lines, report.Words, report.Unique, report.Repeated)
}
