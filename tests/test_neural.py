import unittest

import torch

from proton.model import ProtonTransformer
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


if __name__ == "__main__":
    unittest.main()
