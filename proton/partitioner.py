"""Resource partitioning for Proton's concurrent agent team.

The partitioner allocates explicit RAM, CPU and optional GPU-memory budgets.
It is a scheduler component, not a model or an inference engine.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


MIB = 1024 * 1024


@dataclass(frozen=True)
class ResourceSnapshot:
    """A point-in-time resource snapshot supplied by the host adapter."""

    ram_total_bytes: int
    ram_available_bytes: int
    cpu_cores: float
    gpu_memory_available_bytes: int = 0
    thermal_state: str = "normal"

    def validate(self) -> None:
        if self.ram_total_bytes <= 0:
            raise ValueError("ram_total_bytes must be positive")
        if not 0 <= self.ram_available_bytes <= self.ram_total_bytes:
            raise ValueError("ram_available_bytes must be between zero and total RAM")
        if self.cpu_cores <= 0:
            raise ValueError("cpu_cores must be positive")
        if self.gpu_memory_available_bytes < 0:
            raise ValueError("gpu_memory_available_bytes cannot be negative")
        if self.thermal_state not in {"normal", "warm", "hot", "critical", "unknown"}:
            raise ValueError("unsupported thermal_state")


@dataclass(frozen=True)
class AgentDemand:
    """Minimum and preferred resources requested by one agent or task part."""

    agent_id: str
    role: str
    min_ram_bytes: int
    preferred_ram_bytes: int
    cpu_weight: float = 1.0
    gpu_memory_bytes: int = 0
    priority: int = 0
    can_fallback_to_cpu: bool = True

    def validate(self) -> None:
        if not self.agent_id.strip():
            raise ValueError("agent_id cannot be empty")
        if not self.role.strip():
            raise ValueError("role cannot be empty")
        if self.min_ram_bytes <= 0:
            raise ValueError("min_ram_bytes must be positive")
        if self.preferred_ram_bytes < self.min_ram_bytes:
            raise ValueError("preferred_ram_bytes cannot be below min_ram_bytes")
        if self.cpu_weight <= 0:
            raise ValueError("cpu_weight must be positive")
        if self.gpu_memory_bytes < 0:
            raise ValueError("gpu_memory_bytes cannot be negative")


@dataclass(frozen=True)
class AgentAllocation:
    agent_id: str
    role: str
    admitted: bool
    ram_bytes: int
    cpu_cores: float
    gpu_memory_bytes: int
    reason: str


@dataclass(frozen=True)
class PartitionResult:
    allocations: tuple[AgentAllocation, ...]
    ram_budget_bytes: int
    cpu_budget_cores: float
    gpu_budget_bytes: int

    @property
    def admitted(self) -> tuple[AgentAllocation, ...]:
        return tuple(item for item in self.allocations if item.admitted)

    @property
    def rejected(self) -> tuple[AgentAllocation, ...]:
        return tuple(item for item in self.allocations if not item.admitted)


def partition_resources(
    snapshot: ResourceSnapshot,
    demands: Iterable[AgentDemand],
    *,
    os_reserve_fraction: float = 0.25,
    ram_safety_margin_bytes: int = 512 * MIB,
    cpu_utilization_cap: float = 0.75,
    max_agents: int | None = None,
) -> PartitionResult:
    """Allocate bounded resources, preserving an OS reserve and stable priorities.

    Minimum RAM is granted first in descending priority order. Remaining RAM is
    distributed toward preferred amounts using each demand's CPU weight. CPU
    shares are proportional and their sum never exceeds the configured cap.
    GPU requests that cannot be met fall back to CPU only when permitted.
    """
    snapshot.validate()
    requests = list(demands)
    for request in requests:
        request.validate()
    if len({item.agent_id for item in requests}) != len(requests):
        raise ValueError("agent_id values must be unique")
    if not 0.0 <= os_reserve_fraction < 0.9:
        raise ValueError("os_reserve_fraction must be in [0, 0.9)")
    if ram_safety_margin_bytes < 0:
        raise ValueError("ram_safety_margin_bytes cannot be negative")
    if not 0.0 < cpu_utilization_cap <= 1.0:
        raise ValueError("cpu_utilization_cap must be in (0, 1]")
    if max_agents is not None and max_agents < 1:
        raise ValueError("max_agents must be positive")

    reserve_limit = int(snapshot.ram_total_bytes * (1.0 - os_reserve_fraction))
    ram_budget = max(0, min(snapshot.ram_available_bytes, reserve_limit) - ram_safety_margin_bytes)
    cpu_cap = cpu_utilization_cap
    if snapshot.thermal_state == "warm":
        cpu_cap = min(cpu_cap, 0.60)
    elif snapshot.thermal_state == "hot":
        cpu_cap = min(cpu_cap, 0.35)
    elif snapshot.thermal_state in {"critical", "unknown"}:
        cpu_cap = min(cpu_cap, 0.20)
    cpu_budget = snapshot.cpu_cores * cpu_cap
    gpu_budget = int(snapshot.gpu_memory_available_bytes * 0.80)

    ordered = sorted(enumerate(requests), key=lambda pair: (-pair[1].priority, pair[0]))
    remaining_ram = ram_budget
    remaining_gpu = gpu_budget
    selected: list[tuple[int, AgentDemand, int, int, str]] = []
    rejected: dict[int, AgentAllocation] = {}

    for original_index, request in ordered:
        if max_agents is not None and len(selected) >= max_agents:
            rejected[original_index] = AgentAllocation(
                request.agent_id, request.role, False, 0, 0.0, 0,
                "Concurrency limit reached; task remains queued.",
            )
            continue
        if remaining_ram < request.min_ram_bytes:
            rejected[original_index] = AgentAllocation(
                request.agent_id, request.role, False, 0, 0.0, 0,
                "Insufficient safe RAM; task remains queued.",
            )
            continue

        gpu_grant = 0
        reason = "Minimum resources granted."
        if request.gpu_memory_bytes:
            if remaining_gpu >= request.gpu_memory_bytes:
                gpu_grant = request.gpu_memory_bytes
                remaining_gpu -= gpu_grant
            elif request.can_fallback_to_cpu:
                reason = "GPU budget unavailable; admitted with CPU fallback."
            else:
                rejected[original_index] = AgentAllocation(
                    request.agent_id, request.role, False, 0, 0.0, 0,
                    "Required GPU memory unavailable; task remains queued.",
                )
                continue

        remaining_ram -= request.min_ram_bytes
        selected.append((original_index, request, request.min_ram_bytes, gpu_grant, reason))

    # Share spare RAM only among admitted agents, without exceeding preferences.
    spare_ram = remaining_ram
    while spare_ram > 0:
        eligible = [
            item for item in selected
            if item[2] < item[1].preferred_ram_bytes
        ]
        if not eligible:
            break
        total_weight = sum(item[1].cpu_weight for item in eligible)
        progressed = 0
        updated = []
        for original_index, request, granted, gpu_grant, reason in selected:
            if granted >= request.preferred_ram_bytes:
                updated.append((original_index, request, granted, gpu_grant, reason))
                continue
            share = max(1, int(spare_ram * request.cpu_weight / total_weight))
            extra = min(share, request.preferred_ram_bytes - granted, spare_ram)
            updated.append((original_index, request, granted + extra, gpu_grant, reason))
            progressed += extra
            spare_ram -= extra
            if spare_ram <= 0:
                break
        # Keep any entries not visited if the budget was exhausted mid-pass.
        if len(updated) < len(selected):
            updated.extend(selected[len(updated):])
        selected = updated
        if progressed == 0:
            break

    total_weight = sum(item[1].cpu_weight for item in selected)
    allocations_by_index: dict[int, AgentAllocation] = dict(rejected)
    for original_index, request, ram_grant, gpu_grant, reason in selected:
        cpu_share = cpu_budget * request.cpu_weight / total_weight if total_weight else 0.0
        allocations_by_index[original_index] = AgentAllocation(
            request.agent_id, request.role, True, ram_grant,
            cpu_share, gpu_grant, reason,
        )

    return PartitionResult(
        allocations=tuple(allocations_by_index[index] for index in range(len(requests))),
        ram_budget_bytes=ram_budget,
        cpu_budget_cores=cpu_budget,
        gpu_budget_bytes=gpu_budget,
    )
