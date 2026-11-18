package main

import "testing"

func TestValidateCorpus(t *testing.T) {
	if err := validateCorpus("short"); err == nil {
		t.Fatal("expected short corpus to fail")
	}
	valid := "Proton learns from reviewed examples. " +
		"Training data should be lawful, relevant, diverse, and checked. " +
		"Validation data is kept separate from training data."
	if err := validateCorpus(valid); err != nil {
		t.Fatalf("valid corpus rejected: %v", err)
	}
}
