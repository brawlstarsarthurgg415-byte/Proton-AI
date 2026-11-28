import unittest

from proton.partitioner import (
    AgentDemand,
    ResourceSnapshot,
    MIB,
    partition_resources,
)


class PartitionerTests(unittest.TestCase):
    def setUp(self):
        self.snapshot = ResourceSnapshot(
            ram_total_bytes=8 * 1024 * MIB,
            ram_available_bytes=6 * 1024 * MIB,
            cpu_cores=8,
            gpu_memory_available_bytes=2 * 1024 * MIB,
        )

    def test_keeps_os_reserve_and_respects_ram_budget(self):
        demands = [
            AgentDemand("thinker", "pensadora", MIB, 2 * MIB, priority=100),
            AgentDemand("analyst", "analisador", MIB, 2 * MIB, priority=90),
            AgentDemand("worker-1", "executor", MIB, 2 * MIB),
        ]
        result = partition_resources(self.snapshot, demands)
        self.assertTrue(all(item.admitted for item in result.allocations))
        self.assertLessEqual(sum(item.ram_bytes for item in result.admitted), result.ram_budget_bytes)
        self.assertEqual(result.ram_budget_bytes, 6 * 1024 * MIB - 512 * MIB)

    def test_priority_decides_when_minimum_ram_is_scarce(self):
        snapshot = ResourceSnapshot(
            ram_total_bytes=2 * 1024 * MIB,
            ram_available_bytes=1024 * MIB,
            cpu_cores=4,
        )
        demands = [
            AgentDemand("executor", "executor", 700 * MIB, 700 * MIB, priority=1),
            AgentDemand("thinker", "pensadora", 700 * MIB, 700 * MIB, priority=100),
        ]
        result = partition_resources(snapshot, demands, ram_safety_margin_bytes=0)
        by_id = {item.agent_id: item for item in result.allocations}
        self.assertTrue(by_id["thinker"].admitted)
        self.assertFalse(by_id["executor"].admitted)

    def test_gpu_request_falls_back_to_cpu_when_allowed(self):
        demand = AgentDemand(
            "researcher", "pesquisador", MIB, MIB,
            gpu_memory_bytes=3 * 1024 * MIB, can_fallback_to_cpu=True,
        )
        result = partition_resources(self.snapshot, [demand])
        self.assertTrue(result.allocations[0].admitted)
        self.assertEqual(result.allocations[0].gpu_memory_bytes, 0)
        self.assertIn("CPU fallback", result.allocations[0].reason)

    def test_required_gpu_memory_can_queue_agent(self):
        demand = AgentDemand(
            "gpu-worker", "executor", MIB, MIB,
            gpu_memory_bytes=3 * 1024 * MIB, can_fallback_to_cpu=False,
        )
        result = partition_resources(self.snapshot, [demand])
        self.assertFalse(result.allocations[0].admitted)

    def test_hot_device_reduces_cpu_budget(self):
        snapshot = ResourceSnapshot(
            ram_total_bytes=8 * 1024 * MIB,
            ram_available_bytes=6 * 1024 * MIB,
            cpu_cores=8,
            thermal_state="hot",
        )
        result = partition_resources(
            snapshot, [AgentDemand("a", "executor", MIB, MIB)]
        )
        self.assertAlmostEqual(result.cpu_budget_cores, 2.8)

    def test_max_agents_queues_extra_work(self):
        demands = [
            AgentDemand("a", "executor", MIB, MIB),
            AgentDemand("b", "executor", MIB, MIB),
        ]
        result = partition_resources(self.snapshot, demands, max_agents=1)
        self.assertEqual(len(result.admitted), 1)
        self.assertEqual(len(result.rejected), 1)

    def test_duplicate_agent_ids_are_rejected(self):
        demands = [
            AgentDemand("same", "executor", MIB, MIB),
            AgentDemand("same", "executor", MIB, MIB),
        ]
        with self.assertRaises(ValueError):
            partition_resources(self.snapshot, demands)

    def test_invalid_resource_snapshot_is_rejected(self):
        snapshot = ResourceSnapshot(0, 0, 4)
        with self.assertRaises(ValueError):
            partition_resources(snapshot, [])


if __.areyoumain__ == "__main__":
    unittest.main()
