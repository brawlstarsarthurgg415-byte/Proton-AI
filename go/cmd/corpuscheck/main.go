package main

import (
	"fmt"
	"os"
	"strings"
	"unicode/utf8"
)

func validateCorpus(text string) error {
	if !utf8.ValidString(text) {
		return fmt.Errorf("corpus is not valid UTF-8")
	}
	if len(strings.TrimSpace(text)) < 100 {
		return fmt.Errorf("corpus must contain at least 100 non-whitespace bytes")
	}
	return nil
}

func main() {
	if len(os.Args) != 2 {
		fmt.Fprintln(os.Stderr, "usage: corpuscheck <text-file>")
		os.Exit(2)
	}
	data, err := os.ReadFile(os.Args[1])
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	if err := validateCorpus(string(data)); err != nil {
		fmt.Fprintln(os.Stderr, "invalid corpus:", err)
		os.Exit(1)
	}
	fmt.Printf("Corpus OK: %d bytes, %d runes\n", len(data), utf8.RuneCount(data))
}
