import unittest

import torch

from proton.moe import ProtonMoE, ProtonMoEConfig, TopKMoE


class TestTopKMoE(unittest.TestCase):
    def test_routes_only_to_top_k_experts_and_tracks_load(self):
        layer = TopKMoE(width=16, intermediate=24, experts=4, top_k=2)
        output, auxiliary = layer(torch.randn(2, 3, 16))
        self.assertEqual(output.shape, (2, 3, 16))
        self.assertEqual(auxiliary.ndim, 0)
        self.assertEqual(layer.last_router_stats["tokens"], 6)
        self.assertEqual(sum(layer.last_router_stats["tokens_per_expert"]), 12)

    def test_decoder_forward_and_backward(self):
        config = ProtonMoEConfig(
            vocab_size=64, context_length=16, hidden_size=32,
            num_layers=2, num_heads=4, num_experts=4,
            experts_per_token=2, expert_intermediate_size=48,
        )
        model = ProtonMoE(config)
        tokens = torch.randint(0, 64, (2, 8))
        result = model(tokens)
        self.assertEqual(result["logits"].shape, (2, 8, 64))
        loss = torch.nn.functional.cross_entropy(
            result["logits"][:, :-1].reshape(-1, 64),
            tokens[:, 1:].reshape(-1),
        ) + 0.01 * result["aux_loss"]
        loss.backward()
        self.assertIsNotNone(model.blocks[0].moe.router.weight.grad)
        self.assertEqual(len(result["router_stats"]), 2)

    def test_rejects_invalid_top_k(self):
        with self.assertRaises(ValueError):
            ProtonMoEConfig(num_experts=2, experts_per_token=3).validate()


if __name__ == "__main__":
    unittest.main()
