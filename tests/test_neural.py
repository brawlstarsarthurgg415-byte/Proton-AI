import tempfile
import unittest
from pathlib import Path

import torch

from proton.model import ProtonTransformer
from proton.train import encode_corpus, sample_batch, train
from proton.teachers import available_teachers


class NeuralCoreTests(unittest.TestCase):
    def test_forward_shape(self):
        model = ProtonTransformer(vocab_size=32, block_size=16, width=32, heads=4, layers=1)
        tokens = torch.randint(0, 32, (2, 8))
        self.assertEqual(tuple(model(tokens).shape), (2, 8, 32))

    def test_weights_can_be_updated(self):
        model = ProtonTransformer(vocab_size=16, block_size=8, width=16, heads=4, layers=1)
        optimizer = torch.optim.AdamW(model.parameters(), lr=0.01)
        tokens = torch.randint(0, 16, (2, 8))
        before = model.token.weight.detach().clone()
        loss = torch.nn.functional.cross_entropy(model(tokens).reshape(-1, 16), tokens.reshape(-1))
        loss.backward()
        optimizer.step()
        self.assertFalse(torch.equal(before, model.token.weight.detach()))

    def test_teacher_roles_are_separate(self):
        teachers = available_teachers()
        self.assertEqual({teacher.name for teacher in teachers}, {"general", "programming", "science"})

    def test_corpus_is_split_without_overlap(self):
        text = ("Proton learns from examples. " * 20)
        chars, stoi, train_data, val_data = encode_corpus(text)
        self.assertGreater(len(chars), 5)
        self.assertEqual(len(stoi), len(chars))
        self.assertEqual(len(train_data) + len(val_data), len(text))

    def test_batch_has_fixed_shape(self):
        data = torch.arange(100)
        x, y = sample_batch(data, batch_size=4, block_size=12, device="cpu")
        self.assertEqual(tuple(x.shape), (4, 12))
        self.assertTrue(torch.equal(x[:, 1:], y[:, :-1]))

    def test_training_saves_checkpoint_and_validation(self):
        text = ("Proton is learning. Programming uses algorithms. Science studies evidence. " * 8)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = root / "corpus.txt"
            data.write_text(text, encoding="utf-8")
            checkpoint = train(
                hours=0.1, data_path=data, out_dir=root / "checkpoints",
                max_steps=2, device_name="cpu", block_size=8, width=16,
                layers=1, heads=4, batch_size=2, eval_interval=1,
            )
            self.assertTrue(checkpoint.is_file())
            saved = torch.load(checkpoint, map_location="cpu", weights_only=False)
            self.assertEqual(saved["step"], 2)
            self.assertIn("validation", saved["metrics"])
            self.assertIn("optimizer", saved)


if __name__ == "__main__":
    unittest.main()
