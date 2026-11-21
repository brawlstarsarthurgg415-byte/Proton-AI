import json
import tempfile
import unittest
from pathlib import Path

from proton.research_search import format_research_results, search_research_library


class ResearchSearchTests(unittest.TestCase):
    def test_search_finds_relevant_page_and_keeps_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "library.jsonl"
            records = [
                {
                    "title": "Programação imperativa",
                    "topic": "fundamentos de programação",
                    "extract": "Programação imperativa descreve programas por comandos e alterações de estado. " * 3,
                    "url": "https://pt.wikipedia.org/wiki/Programa%C3%A7%C3%A3o_imperativa",
                },
                {
                    "title": "Biologia celular",
                    "topic": "biologia",
                    "extract": "A célula é a unidade estrutural e funcional dos seres vivos. " * 3,
                    "url": "https://pt.wikipedia.org/wiki/C%C3%A9lula",
                },
            ]
            path.write_text("\n".join(json.dumps(item, ensure_ascii=False) for item in records),
                            encoding="utf-8")
            results = search_research_library("o que é programação imperativa", path=path)
            self.assertTrue(results)
            self.assertEqual(results[0]["title"], "Programação imperativa")
            rendered = format_research_results(results)
            self.assertIn("não verificados", rendered)
            self.assertIn(records[0]["url"], rendered)

    def test_bad_json_and_missing_file_are_safe(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "library.jsonl"
            path.write_text("{not json}\n", encoding="utf-8")
            self.assertEqual(search_research_library("astronomia", path=path), [])
            self.assertEqual(search_research_library("astronomia", path=path.parent / "missing.jsonl"), [])

    def test_empty_query_and_invalid_limit(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "library.jsonl"
            path.write_text("", encoding="utf-8")
            self.assertEqual(search_research_library("   ", path=path), [])
            with self.assertRaises(ValueError):
                search_research_library("teste", path=path, limit=0)


if __name__ == "__main__":
    unittest.main()
