package main

import (
	"strings"
	"testing"
	"unicode/utf8"
)

func TestAnalyzeCountsAndRepetition(t *testing.T) {
	r, err := Analyze("sample.txt", []byte("Proton learns. Proton tests."))
	if err != nil { t.Fatal(err) }
	if r.Words != 4 || r.Unique != 3 || r.Repeated != 1 || r.Lines != 1 { t.Fatalf("unexpected report: %+v", r) }
}

func TestAnalyzeRejectsInvalidUTF8(t *testing.T) {
	_, err := Analyze("bad.txt", []byte{0xff, 0xfe})
	if err == nil || !strings.Contains(err.Error(), "UTF-8") { t.Fatalf("expected UTF-8 error, got %v", err) }
}

func TestAnalyzeRejectsEmpty(t *testing.T) {
	_, err := Analyze("empty.txt", []byte(" \n\t"))
	if err == nil { t.Fatal("expected empty corpus to fail") }
}

func TestAnalyzeCountsUnicodeCharacters(t *testing.T) {
	r, err := Analyze("unicode.txt", []byte("ação ciência"))
	if err != nil { t.Fatal(err) }
	if !utf8.Valid([]byte("ação")) || r.Characters != 12 { t.Fatalf("unexpected unicode report: %+v", r) }
}
