"""
Functional test based on Vajra's configuration hierarchy.

This test validates that vidhi can handle a real-world complex config structure
with multiple polymorphic hierarchies, deep nesting, and CLI argument generation.

Patterns covered from vajra:
- Polymorphic config hierarchies with enum type discriminators
- Native handle pattern (simulated without C++ bindings)
- Computed fields set in __post_init__
- Cross-field validation (min < max, divisibility checks)
- Properties on frozen dataclasses
- Optional fields with lambda factories
- File path templates with placeholder substitution
- Methods that compute values from nested configs
- Conditional field modification in __post_init__
- Range and positive value validation
"""

from dataclasses import field as dataclass_field
from enum import Enum
from typing import List, Optional

import pytest

from vidhi import (
    BasePolyConfig,
    create_class_from_dict,
    dataclass_to_dict,
    field,
    frozen_dataclass,
)
from vidhi.flat_dataclass import create_flat_dataclass


# =============================================================================
# Enums (mirroring vajra's C++ enums)
# =============================================================================
class AllocatorType(Enum):
    LRU = "lru"
    LFU = "lfu"
    COST_AWARE_EXP_DECAY = "cost_aware_exp_decay"
    COST_AWARE_GDSF = "cost_aware_gdsf"


class ComputeManagerType(Enum):
    FIXED_CHUNK = "fixed_chunk"
    DYNAMIC_CHUNK = "dynamic_chunk"
    SPACE_SHARING = "space_sharing"


class SessionRouterType(Enum):
    PULL = "pull"
    ROUND_ROBIN = "round_robin"


class SessionPrioritizerType(Enum):
    FCFS = "fcfs"
    EDF = "edf"
    LRS = "lrs"


class ResourceAllocatorType(Enum):
    LOCAL = "local"
    RAY = "ray"
    MOCK = "mock"


class ModelConfigType(Enum):
    LLM = "llm"


class ReplicaControllerType(Enum):
    LLM_BASE = "llm_base"


class ReplicasetControllerType(Enum):
    LLM = "llm"


class SchedulerType(Enum):
    GREEDY = "greedy"
    BALANCED = "balanced"
    PRIORITY = "priority"


class StorageBackendType(Enum):
    LOCAL = "local"
    S3 = "s3"
    GCS = "gcs"


# =============================================================================
# Polymorphic Hierarchy 1: Allocator (4 variants)
# =============================================================================
@frozen_dataclass
class AbstractAllocatorConfig(BasePolyConfig):
    """Abstract base for cache allocator configurations."""

    @classmethod
    def get_type(cls) -> AllocatorType:
        raise NotImplementedError()


@frozen_dataclass
class LruAllocatorConfig(AbstractAllocatorConfig):
    """LRU (Least Recently Used) allocator."""

    @staticmethod
    def get_type() -> AllocatorType:
        return AllocatorType.LRU


@frozen_dataclass
class LfuAllocatorConfig(AbstractAllocatorConfig):
    """LFU (Least Frequently Used) allocator."""

    @staticmethod
    def get_type() -> AllocatorType:
        return AllocatorType.LFU


@frozen_dataclass
class CostAwareExpDecayAllocatorConfig(AbstractAllocatorConfig):
    """Cost-aware allocator with exponential decay."""

    prefill_profiling_path: str = field(
        "./profiling.json", help="Path to prefill profiling JSON"
    )
    decay_rate: float = field(0.5, help="Forward decay rate")
    min_cost: float = field(1e-10, help="Minimum cost value")

    @staticmethod
    def get_type() -> AllocatorType:
        return AllocatorType.COST_AWARE_EXP_DECAY

    def __post_init__(self):
        if self.decay_rate <= 0:
            raise ValueError("decay_rate must be positive")
        if self.min_cost <= 0:
            raise ValueError("min_cost must be positive")


@frozen_dataclass
class CostAwareGdsfAllocatorConfig(AbstractAllocatorConfig):
    """Cost-aware allocator with GDSF aging."""

    prefill_profiling_path: str = field(
        "./profiling.json", help="Path to prefill profiling JSON"
    )
    use_frequency: bool = field(True, help="Use GDSF (with frequency) vs GDS")

    @staticmethod
    def get_type() -> AllocatorType:
        return AllocatorType.COST_AWARE_GDSF


# =============================================================================
# Polymorphic Hierarchy 2: Compute Manager (3 variants)
# =============================================================================
@frozen_dataclass
class AbstractComputeManagerConfig(BasePolyConfig):
    """Abstract base for compute manager configurations."""

    @classmethod
    def get_type(cls) -> ComputeManagerType:
        raise NotImplementedError()


@frozen_dataclass
class FixedChunkComputeManagerConfig(AbstractComputeManagerConfig):
    """Fixed chunk compute manager."""

    chunk_size: int = field(2048, help="Fixed chunk size in tokens")

    @staticmethod
    def get_type() -> ComputeManagerType:
        return ComputeManagerType.FIXED_CHUNK


@frozen_dataclass
class DynamicChunkComputeManagerConfig(AbstractComputeManagerConfig):
    """Dynamic chunk compute manager with cross-field validation."""

    min_chunk_size: int = field(512, help="Minimum chunk size")
    max_chunk_size: int = field(4096, help="Maximum chunk size")

    @staticmethod
    def get_type() -> ComputeManagerType:
        return ComputeManagerType.DYNAMIC_CHUNK

    def __post_init__(self):
        # Cross-field validation (vajra pattern: min < max)
        if self.min_chunk_size <= 0:
            raise ValueError("min_chunk_size must be positive")
        if self.max_chunk_size <= 0:
            raise ValueError("max_chunk_size must be positive")
        if self.min_chunk_size >= self.max_chunk_size:
            raise ValueError("min_chunk_size must be less than max_chunk_size")


@frozen_dataclass
class SpaceSharingComputeManagerConfig(AbstractComputeManagerConfig):
    """Space sharing compute manager."""

    max_concurrent_sequences: int = field(8, help="Max concurrent sequences")

    @staticmethod
    def get_type() -> ComputeManagerType:
        return ComputeManagerType.SPACE_SHARING


# =============================================================================
# Polymorphic Hierarchy 3: Session Router (2 variants)
# =============================================================================
@frozen_dataclass
class AbstractSessionRouterConfig(BasePolyConfig):
    """Abstract base for session router configurations."""

    @classmethod
    def get_type(cls) -> SessionRouterType:
        raise NotImplementedError()


@frozen_dataclass
class PullSessionRouterConfig(AbstractSessionRouterConfig):
    """Pull-based session router."""

    @staticmethod
    def get_type() -> SessionRouterType:
        return SessionRouterType.PULL


@frozen_dataclass
class RoundRobinSessionRouterConfig(AbstractSessionRouterConfig):
    """Round-robin session router."""

    @staticmethod
    def get_type() -> SessionRouterType:
        return SessionRouterType.ROUND_ROBIN


# =============================================================================
# Polymorphic Hierarchy 4: Session Prioritizer (3 variants)
# =============================================================================
@frozen_dataclass
class AbstractSessionPrioritizerConfig(BasePolyConfig):
    """Abstract base for session prioritizer configurations."""

    @classmethod
    def get_type(cls) -> SessionPrioritizerType:
        raise NotImplementedError()


@frozen_dataclass
class FcfsSessionPrioritizerConfig(AbstractSessionPrioritizerConfig):
    """First-come-first-served prioritizer."""

    @staticmethod
    def get_type() -> SessionPrioritizerType:
        return SessionPrioritizerType.FCFS


@frozen_dataclass
class EdfSessionPrioritizerConfig(AbstractSessionPrioritizerConfig):
    """Earliest deadline first prioritizer."""

    default_deadline_ms: float = field(1000.0, help="Default deadline in milliseconds")

    @staticmethod
    def get_type() -> SessionPrioritizerType:
        return SessionPrioritizerType.EDF


@frozen_dataclass
class LrsSessionPrioritizerConfig(AbstractSessionPrioritizerConfig):
    """Longest remaining service prioritizer."""

    preemption_threshold: float = field(0.5, help="Preemption threshold")

    @staticmethod
    def get_type() -> SessionPrioritizerType:
        return SessionPrioritizerType.LRS


# =============================================================================
# Polymorphic Hierarchy 5: Resource Allocator (3 variants)
# =============================================================================
@frozen_dataclass
class AbstractResourceAllocatorConfig(BasePolyConfig):
    """Abstract base for resource allocator configurations."""

    @classmethod
    def get_type(cls) -> ResourceAllocatorType:
        raise NotImplementedError()


@frozen_dataclass
class LocalGpuResourceAllocatorConfig(AbstractResourceAllocatorConfig):
    """Local GPU resource allocator."""

    @staticmethod
    def get_type() -> ResourceAllocatorType:
        return ResourceAllocatorType.LOCAL


@frozen_dataclass
class RayGpuResourceAllocatorConfig(AbstractResourceAllocatorConfig):
    """Ray-based GPU resource allocator."""

    ray_address: str = field("auto", help="Ray cluster address")

    @staticmethod
    def get_type() -> ResourceAllocatorType:
        return ResourceAllocatorType.RAY


@frozen_dataclass
class MockResourceAllocatorConfig(AbstractResourceAllocatorConfig):
    """Mock resource allocator for testing."""

    num_mock_gpus: int = field(4, help="Number of mock GPUs")

    @staticmethod
    def get_type() -> ResourceAllocatorType:
        return ResourceAllocatorType.MOCK


# =============================================================================
# Regular (non-polymorphic) nested configs
# =============================================================================
@frozen_dataclass
class CacheTierConfig:
    """Configuration for a single cache tier."""

    admission_watermark: float = field(0.05, help="Admission watermark threshold")
    demotion_watermark: float = field(0.1, help="Demotion watermark threshold")

    def __post_init__(self):
        if not 0 <= self.admission_watermark <= 1:
            raise ValueError("admission_watermark must be between 0 and 1")
        if not 0 <= self.demotion_watermark <= 1:
            raise ValueError("demotion_watermark must be between 0 and 1")
        # Cross-field validation (vajra pattern)
        if self.admission_watermark >= self.demotion_watermark:
            raise ValueError("admission_watermark must be less than demotion_watermark")


@frozen_dataclass
class CacheConfig:
    """Multi-tiered cache configuration."""

    page_size: int = field(16, help="Cache page size in tokens")
    max_promotion_batch_size: int = field(1000, help="Max tokens to promote per batch")
    max_demotion_batch_size: int = field(1000, help="Max tokens to demote per batch")
    allocator: AbstractAllocatorConfig = dataclass_field(
        default_factory=LruAllocatorConfig
    )
    gpu_tier: CacheTierConfig = dataclass_field(default_factory=CacheTierConfig)
    cpu_tier: CacheTierConfig = dataclass_field(default_factory=CacheTierConfig)
    nvme_tier: CacheTierConfig = dataclass_field(default_factory=CacheTierConfig)
    enable_prefix_caching: bool = field(True, help="Enable prefix caching")

    def __post_init__(self):
        if self.page_size <= 0:
            raise ValueError("page_size must be positive")


@frozen_dataclass
class WorkerConfig:
    """Worker process configuration."""

    num_workers: int = field(1, help="Number of worker processes")
    worker_use_ray: bool = field(False, help="Use Ray for workers")


# =============================================================================
# Polymorphic Hierarchy 6: Model Deployment
# =============================================================================
@frozen_dataclass
class AbstractModelDeploymentConfig(BasePolyConfig):
    """Abstract base for model deployment configurations."""

    model: str = field("meta-llama/Llama-3-8B", help="Model name or path")
    tensor_parallel_size: int = field(1, help="Tensor parallel size")
    pipeline_parallel_size: int = field(1, help="Pipeline parallel size")
    max_model_len: int = field(4096, help="Maximum model length")
    seed: int = field(0, help="Random seed")

    @property
    def world_size(self) -> int:
        return self.tensor_parallel_size * self.pipeline_parallel_size

    @classmethod
    def get_type(cls) -> ModelConfigType:
        raise NotImplementedError()


@frozen_dataclass
class ModelDeploymentConfig(AbstractModelDeploymentConfig):
    """LLM model deployment configuration."""

    trust_remote_code: bool = field(True, help="Trust remote code")
    load_format: str = field("safetensors", help="Model weights format")

    @staticmethod
    def get_type() -> ModelConfigType:
        return ModelConfigType.LLM

    def __post_init__(self):
        if self.load_format not in ["safetensors", "dummy"]:
            raise ValueError(f"Invalid load_format: {self.load_format}")


# =============================================================================
# Polymorphic Hierarchy 7: Replica Controller (2 levels deep)
# =============================================================================
@frozen_dataclass
class AbstractReplicaControllerConfig(BasePolyConfig):
    """Abstract base for replica controller configurations."""

    @classmethod
    def get_type(cls) -> ReplicaControllerType:
        raise NotImplementedError()


def _get_default_model_deployment():
    """Lazy import to avoid circular dependencies."""
    return ModelDeploymentConfig()


@frozen_dataclass
class ReplicaControllerConfig(AbstractReplicaControllerConfig):
    """LLM replica controller configuration."""

    model_deployment_config: AbstractModelDeploymentConfig = dataclass_field(
        default_factory=_get_default_model_deployment
    )
    worker_config: WorkerConfig = dataclass_field(default_factory=WorkerConfig)
    cache_config: CacheConfig = dataclass_field(default_factory=CacheConfig)
    compute_manager_config: AbstractComputeManagerConfig = dataclass_field(
        default_factory=FixedChunkComputeManagerConfig
    )

    @staticmethod
    def get_type() -> ReplicaControllerType:
        return ReplicaControllerType.LLM_BASE


# =============================================================================
# Polymorphic Hierarchy 8: Replicaset Controller (3 levels deep)
# =============================================================================
@frozen_dataclass
class AbstractReplicasetControllerConfig(BasePolyConfig):
    """Abstract base for replicaset controller configurations."""

    @classmethod
    def get_type(cls) -> ReplicasetControllerType:
        raise NotImplementedError()


def _get_default_replica_controller():
    return ReplicaControllerConfig()


@frozen_dataclass
class ReplicasetControllerConfig(AbstractReplicasetControllerConfig):
    """LLM replicaset controller configuration."""

    replica_controller_config: AbstractReplicaControllerConfig = dataclass_field(
        default_factory=_get_default_replica_controller
    )
    session_prioritizer_config: AbstractSessionPrioritizerConfig = dataclass_field(
        default_factory=FcfsSessionPrioritizerConfig
    )
    session_router_config: AbstractSessionRouterConfig = dataclass_field(
        default_factory=PullSessionRouterConfig
    )

    @staticmethod
    def get_type() -> ReplicasetControllerType:
        return ReplicasetControllerType.LLM


# =============================================================================
# Top-level config: InferenceEngineConfig
# =============================================================================
def _get_default_replicaset_controller():
    return ReplicasetControllerConfig()


@frozen_dataclass
class MetricsConfig:
    """Metrics configuration."""

    enable_metrics: bool = field(True, help="Enable metrics collection")
    metrics_port: int = field(9090, help="Prometheus metrics port")


@frozen_dataclass
class InferenceEngineConfig:
    """Top-level inference engine configuration."""

    controller_config: AbstractReplicasetControllerConfig = dataclass_field(
        default_factory=_get_default_replicaset_controller
    )
    metrics_config: MetricsConfig = dataclass_field(default_factory=MetricsConfig)
    resource_allocator_config: AbstractResourceAllocatorConfig = dataclass_field(
        default_factory=LocalGpuResourceAllocatorConfig
    )


# =============================================================================
# Additional patterns from vajra: Computed fields, file paths, validation
# =============================================================================
@frozen_dataclass
class ParallelismConfig:
    """Config with computed fields and divisibility validation (vajra pattern)."""

    tensor_parallel: int = field(1, help="Tensor parallel degree")
    pipeline_parallel: int = field(1, help="Pipeline parallel degree")
    data_parallel: int = field(1, help="Data parallel degree")
    # Computed field set in __post_init__
    _total_gpus: int = dataclass_field(default=0, repr=False)

    def __post_init__(self):
        # Positive validation
        if self.tensor_parallel <= 0:
            raise ValueError("tensor_parallel must be positive")
        if self.pipeline_parallel <= 0:
            raise ValueError("pipeline_parallel must be positive")
        if self.data_parallel <= 0:
            raise ValueError("data_parallel must be positive")
        # Compute derived field (vajra pattern)
        object.__setattr__(
            self,
            "_total_gpus",
            self.tensor_parallel * self.pipeline_parallel * self.data_parallel,
        )

    @property
    def total_gpus(self) -> int:
        """Total GPUs required."""
        return self._total_gpus

    @property
    def world_size(self) -> int:
        """Alias for total_gpus."""
        return self._total_gpus

    def verify_parallelism(self, available_gpus: int) -> bool:
        """Verify parallelism config fits available resources."""
        return self._total_gpus <= available_gpus


@frozen_dataclass
class BatchConfig:
    """Config with cross-field validation and divisibility checks (vajra pattern)."""

    min_batch_size: int = field(1, help="Minimum batch size")
    max_batch_size: int = field(64, help="Maximum batch size")
    batch_size_step: int = field(1, help="Batch size increment step")

    def __post_init__(self):
        # Positive validation
        if self.min_batch_size <= 0:
            raise ValueError("min_batch_size must be positive")
        if self.max_batch_size <= 0:
            raise ValueError("max_batch_size must be positive")
        if self.batch_size_step <= 0:
            raise ValueError("batch_size_step must be positive")
        # Cross-field: min < max
        if self.min_batch_size > self.max_batch_size:
            raise ValueError("min_batch_size must be <= max_batch_size")
        # Divisibility check (vajra pattern)
        range_size = self.max_batch_size - self.min_batch_size
        if range_size > 0 and range_size % self.batch_size_step != 0:
            raise ValueError(
                f"batch size range ({range_size}) must be divisible by step ({self.batch_size_step})"
            )


@frozen_dataclass
class FilePathConfig:
    """Config with file path templates (vajra pattern)."""

    base_dir: str = field("/data", help="Base directory")
    model_name: str = field("llama", help="Model name")
    checkpoint_subdir: str = field("checkpoints", help="Checkpoint subdirectory")
    log_subdir: str = field("logs", help="Log subdirectory")

    @property
    def checkpoint_dir(self) -> str:
        """Computed checkpoint directory path."""
        return f"{self.base_dir}/{self.model_name}/{self.checkpoint_subdir}"

    @property
    def log_dir(self) -> str:
        """Computed log directory path."""
        return f"{self.base_dir}/{self.model_name}/{self.log_subdir}"

    def get_checkpoint_path(self, step: int) -> str:
        """Get path for specific checkpoint step."""
        return f"{self.checkpoint_dir}/step_{step}.pt"

    def get_log_path(self, name: str) -> str:
        """Get path for specific log file."""
        return f"{self.log_dir}/{name}.log"


@frozen_dataclass
class MemoryConfig:
    """Config with conditional field modification in __post_init__ (vajra pattern)."""

    gpu_memory_fraction: float = field(0.9, help="Fraction of GPU memory to use")
    cpu_memory_gb: Optional[int] = field(None, help="CPU memory limit (None=auto)")
    swap_space_gb: int = field(0, help="Swap space in GB")
    # Computed field
    _effective_cpu_memory_gb: int = dataclass_field(default=0, repr=False)

    def __post_init__(self):
        if not 0 < self.gpu_memory_fraction <= 1:
            raise ValueError("gpu_memory_fraction must be in (0, 1]")
        if self.swap_space_gb < 0:
            raise ValueError("swap_space_gb must be non-negative")
        # Conditional field modification (vajra pattern)
        # If cpu_memory_gb is None, auto-detect (simulated as 64GB)
        effective = self.cpu_memory_gb if self.cpu_memory_gb is not None else 64
        object.__setattr__(self, "_effective_cpu_memory_gb", effective)

    @property
    def effective_cpu_memory_gb(self) -> int:
        return self._effective_cpu_memory_gb

    @property
    def total_memory_gb(self) -> int:
        """Total memory including swap."""
        return self._effective_cpu_memory_gb + self.swap_space_gb


# =============================================================================
# Polymorphic Hierarchy: Scheduler (with methods using computed fields)
# =============================================================================
@frozen_dataclass
class AbstractSchedulerConfig(BasePolyConfig):
    """Abstract base for scheduler configurations."""

    max_pending_requests: int = field(1000, help="Max pending requests")

    @classmethod
    def get_type(cls) -> SchedulerType:
        raise NotImplementedError()


@frozen_dataclass
class GreedySchedulerConfig(AbstractSchedulerConfig):
    """Greedy scheduler that processes requests immediately."""

    @staticmethod
    def get_type() -> SchedulerType:
        return SchedulerType.GREEDY


@frozen_dataclass
class BalancedSchedulerConfig(AbstractSchedulerConfig):
    """Balanced scheduler with load balancing."""

    balance_interval_ms: int = field(100, help="Load balance interval in ms")
    max_imbalance_ratio: float = field(0.2, help="Max allowed imbalance ratio")

    @staticmethod
    def get_type() -> SchedulerType:
        return SchedulerType.BALANCED

    def __post_init__(self):
        if self.balance_interval_ms <= 0:
            raise ValueError("balance_interval_ms must be positive")
        if not 0 < self.max_imbalance_ratio < 1:
            raise ValueError("max_imbalance_ratio must be in (0, 1)")


@frozen_dataclass
class PrioritySchedulerConfig(AbstractSchedulerConfig):
    """Priority-based scheduler with multiple priority levels."""

    num_priority_levels: int = field(3, help="Number of priority levels")
    preemption_enabled: bool = field(True, help="Enable request preemption")
    starvation_timeout_ms: int = field(5000, help="Starvation prevention timeout")

    @staticmethod
    def get_type() -> SchedulerType:
        return SchedulerType.PRIORITY

    def __post_init__(self):
        if self.num_priority_levels < 1:
            raise ValueError("num_priority_levels must be at least 1")
        if self.starvation_timeout_ms <= 0:
            raise ValueError("starvation_timeout_ms must be positive")


# =============================================================================
# Polymorphic Hierarchy: Storage Backend (file paths and optional fields)
# =============================================================================
@frozen_dataclass
class AbstractStorageBackendConfig(BasePolyConfig):
    """Abstract base for storage backend configurations."""

    @classmethod
    def get_type(cls) -> StorageBackendType:
        raise NotImplementedError()


@frozen_dataclass
class LocalStorageConfig(AbstractStorageBackendConfig):
    """Local filesystem storage."""

    root_path: str = field("/data/storage", help="Root storage path")
    max_size_gb: Optional[int] = field(None, help="Max size limit (None=unlimited)")

    @staticmethod
    def get_type() -> StorageBackendType:
        return StorageBackendType.LOCAL

    def get_full_path(self, relative_path: str) -> str:
        """Get full path from relative path."""
        return f"{self.root_path}/{relative_path}"


@frozen_dataclass
class S3StorageConfig(AbstractStorageBackendConfig):
    """AWS S3 storage backend."""

    bucket: str = field("my-bucket", help="S3 bucket name")
    prefix: str = field("", help="Key prefix")
    region: str = field("us-east-1", help="AWS region")
    endpoint_url: Optional[str] = field(None, help="Custom endpoint URL")

    @staticmethod
    def get_type() -> StorageBackendType:
        return StorageBackendType.S3

    def get_full_key(self, key: str) -> str:
        """Get full S3 key with prefix."""
        if self.prefix:
            return f"{self.prefix}/{key}"
        return key


@frozen_dataclass
class GCSStorageConfig(AbstractStorageBackendConfig):
    """Google Cloud Storage backend."""

    bucket: str = field("my-bucket", help="GCS bucket name")
    prefix: str = field("", help="Object prefix")
    project: Optional[str] = field(None, help="GCP project ID")

    @staticmethod
    def get_type() -> StorageBackendType:
        return StorageBackendType.GCS


# =============================================================================
# Complex nested config with multiple computed fields
# =============================================================================
@frozen_dataclass
class TrainingConfig:
    """Complex training config with multiple computed fields (vajra pattern)."""

    parallelism: ParallelismConfig = dataclass_field(default_factory=ParallelismConfig)
    batch: BatchConfig = dataclass_field(default_factory=BatchConfig)
    memory: MemoryConfig = dataclass_field(default_factory=MemoryConfig)
    paths: FilePathConfig = dataclass_field(default_factory=FilePathConfig)
    scheduler: AbstractSchedulerConfig = dataclass_field(
        default_factory=GreedySchedulerConfig
    )
    storage: AbstractStorageBackendConfig = dataclass_field(
        default_factory=LocalStorageConfig
    )
    # Training hyperparameters
    learning_rate: float = field(1e-4, help="Learning rate")
    num_epochs: int = field(10, help="Number of training epochs")
    gradient_accumulation_steps: int = field(1, help="Gradient accumulation steps")
    # Computed field
    _effective_batch_size: int = dataclass_field(default=0, repr=False)

    def __post_init__(self):
        if self.learning_rate <= 0:
            raise ValueError("learning_rate must be positive")
        if self.num_epochs <= 0:
            raise ValueError("num_epochs must be positive")
        if self.gradient_accumulation_steps <= 0:
            raise ValueError("gradient_accumulation_steps must be positive")
        # Compute effective batch size (vajra pattern)
        effective = (
            self.batch.max_batch_size
            * self.parallelism.data_parallel
            * self.gradient_accumulation_steps
        )
        object.__setattr__(self, "_effective_batch_size", effective)

    @property
    def effective_batch_size(self) -> int:
        """Effective batch size across all data parallel workers."""
        return self._effective_batch_size

    def get_checkpoint_path(self, epoch: int) -> str:
        """Get checkpoint path for specific epoch."""
        return self.paths.get_checkpoint_path(epoch)

    def validate_resources(self, available_gpus: int) -> bool:
        """Validate that training config fits available resources."""
        return self.parallelism.verify_parallelism(available_gpus)


# =============================================================================
# Config with list of polymorphic configs
# =============================================================================
@frozen_dataclass
class MultiModelConfig:
    """Config with list of polymorphic model configs."""

    models: List[AbstractModelDeploymentConfig] = dataclass_field(default_factory=list)
    default_model_index: int = field(0, help="Index of default model")

    def __post_init__(self):
        if self.models and not 0 <= self.default_model_index < len(self.models):
            raise ValueError(
                f"default_model_index {self.default_model_index} out of range"
            )

    @property
    def default_model(self) -> Optional[AbstractModelDeploymentConfig]:
        """Get the default model config."""
        if not self.models:
            return None
        return self.models[self.default_model_index]

    @property
    def total_world_size(self) -> int:
        """Total world size across all models."""
        return sum(m.world_size for m in self.models)


# =============================================================================
# Tests
# =============================================================================
class TestVajraConfigHierarchy:
    """Test the vajra-like config hierarchy."""

    def test_default_instantiation(self):
        """Test that all configs can be instantiated with defaults."""
        config = InferenceEngineConfig()

        # Check nested structure
        assert isinstance(config.controller_config, AbstractReplicasetControllerConfig)
        assert isinstance(config.controller_config, ReplicasetControllerConfig)
        assert isinstance(
            config.controller_config.replica_controller_config,
            ReplicaControllerConfig,
        )
        assert isinstance(
            config.controller_config.replica_controller_config.model_deployment_config,
            ModelDeploymentConfig,
        )

    def test_polymorphic_type_resolution(self):
        """Test polymorphic type resolution via create_from_type."""
        # Allocator
        lru = AbstractAllocatorConfig.create_from_type(AllocatorType.LRU)
        assert isinstance(lru, LruAllocatorConfig)

        lfu = AbstractAllocatorConfig.create_from_type(AllocatorType.LFU)
        assert isinstance(lfu, LfuAllocatorConfig)

        # Compute manager
        fixed = AbstractComputeManagerConfig.create_from_type(
            ComputeManagerType.FIXED_CHUNK
        )
        assert isinstance(fixed, FixedChunkComputeManagerConfig)

        # Resource allocator
        ray = AbstractResourceAllocatorConfig.create_from_type(
            ResourceAllocatorType.RAY
        )
        assert isinstance(ray, RayGpuResourceAllocatorConfig)

    def test_create_from_dict_simple(self):
        """Test creating configs from dict."""
        config_dict = {
            "type": "cost_aware_exp_decay",
            "prefill_profiling_path": "/custom/path.json",
            "decay_rate": 0.8,
        }
        config = create_class_from_dict(AbstractAllocatorConfig, config_dict)
        assert isinstance(config, CostAwareExpDecayAllocatorConfig)
        assert config.prefill_profiling_path == "/custom/path.json"
        assert config.decay_rate == 0.8

    def test_create_from_dict_nested(self):
        """Test creating nested configs from dict."""
        config_dict = {
            "page_size": 32,
            "allocator": {"type": "lfu"},
            "gpu_tier": {"admission_watermark": 0.1, "demotion_watermark": 0.2},
        }
        config = create_class_from_dict(CacheConfig, config_dict)
        assert config.page_size == 32
        assert isinstance(config.allocator, LfuAllocatorConfig)
        assert config.gpu_tier.admission_watermark == 0.1

    def test_create_from_dict_deep_nesting(self):
        """Test creating deeply nested configs from dict."""
        config_dict = {
            "controller_config": {
                "type": "llm",
                "replica_controller_config": {
                    "type": "llm_base",
                    "model_deployment_config": {
                        "type": "llm",
                        "model": "custom-model",
                        "tensor_parallel_size": 4,
                    },
                    "cache_config": {
                        "page_size": 64,
                        "allocator": {"type": "cost_aware_gdsf"},
                    },
                },
            },
            "resource_allocator_config": {"type": "mock", "num_mock_gpus": 8},
        }

        config = create_class_from_dict(InferenceEngineConfig, config_dict)

        # Verify deep nesting
        assert (
            config.controller_config.replica_controller_config.model_deployment_config.model
            == "custom-model"
        )
        assert (
            config.controller_config.replica_controller_config.model_deployment_config.tensor_parallel_size
            == 4
        )
        assert (
            config.controller_config.replica_controller_config.cache_config.page_size
            == 64
        )
        assert isinstance(
            config.controller_config.replica_controller_config.cache_config.allocator,
            CostAwareGdsfAllocatorConfig,
        )
        assert isinstance(config.resource_allocator_config, MockResourceAllocatorConfig)
        assert config.resource_allocator_config.num_mock_gpus == 8

    def test_dataclass_to_dict_roundtrip(self):
        """Test conversion to dict and back."""
        original = InferenceEngineConfig()
        as_dict = dataclass_to_dict(original)

        # Verify structure
        assert "controller_config" in as_dict
        assert "type" in as_dict["controller_config"]

        # Roundtrip
        reconstructed = create_class_from_dict(InferenceEngineConfig, as_dict)
        assert (
            reconstructed.controller_config.replica_controller_config.model_deployment_config.model
            == original.controller_config.replica_controller_config.model_deployment_config.model
        )

    def test_validation_in_post_init(self):
        """Test that validation in __post_init__ works."""
        # Valid
        config = CostAwareExpDecayAllocatorConfig(decay_rate=0.5)
        assert config.decay_rate == 0.5

        # Invalid
        with pytest.raises(ValueError, match="decay_rate must be positive"):
            CostAwareExpDecayAllocatorConfig(decay_rate=-0.5)

        with pytest.raises(ValueError, match="admission_watermark"):
            CacheTierConfig(admission_watermark=1.5)

    def test_computed_properties(self):
        """Test that computed properties work."""
        config = ModelDeploymentConfig(tensor_parallel_size=4, pipeline_parallel_size=2)
        assert config.world_size == 8

    def test_immutability(self):
        """Test that configs are frozen."""
        config = InferenceEngineConfig()
        with pytest.raises(AttributeError):
            config.metrics_config = MetricsConfig()


class TestVajraConfigCLI:
    """Test CLI argument generation for vajra-like configs."""

    def test_flat_dataclass_creation(self):
        """Test that flat dataclass can be created."""
        FlatConfig = create_flat_dataclass(InferenceEngineConfig)
        assert FlatConfig is not None

    def test_cli_args_parsing(self):
        """Test that CLI args can be generated for nested config.

        Note: The args parameter in parse_cli_args is reserved for future use.
        This test validates that the flat dataclass structure is correct.
        """
        # For now, just verify the flat dataclass has the expected structure
        FlatConfig = create_flat_dataclass(InferenceEngineConfig)
        field_names = [f.name for f in FlatConfig.__dataclass_fields__.values()]

        # Should have nested config references for polymorphic fields
        assert any("controller_config" in name for name in field_names)
        assert any("resource_allocator_config" in name for name in field_names)

    def test_polymorphic_type_selection_cli(self):
        """Test polymorphic type selection via CLI."""
        FlatConfig = create_flat_dataclass(CacheConfig)

        # The flat config should have a type field for allocator
        field_names = [f.name for f in FlatConfig.__dataclass_fields__.values()]
        assert "allocator__type" in field_names or "allocator_type" in field_names


class TestVajraConfigEdgeCases:
    """Test edge cases in the config hierarchy."""

    def test_all_allocator_types(self):
        """Test all allocator type variants."""
        for alloc_type in AllocatorType:
            config = AbstractAllocatorConfig.create_from_type(alloc_type)
            assert config.get_type() == alloc_type

    def test_all_compute_manager_types(self):
        """Test all compute manager variants."""
        for cm_type in ComputeManagerType:
            config = AbstractComputeManagerConfig.create_from_type(cm_type)
            assert config.get_type() == cm_type

    def test_string_type_resolution(self):
        """Test that string type values work."""
        config = AbstractAllocatorConfig.create_from_type("lru")
        assert isinstance(config, LruAllocatorConfig)

        config = AbstractAllocatorConfig.create_from_type("LRU")  # case insensitive
        assert isinstance(config, LruAllocatorConfig)

    def test_empty_polymorphic_config(self):
        """Test polymorphic configs with no extra fields."""
        config = LruAllocatorConfig()
        assert config.get_type() == AllocatorType.LRU

        config = PullSessionRouterConfig()
        assert config.get_type() == SessionRouterType.PULL

    def test_nested_default_factories(self):
        """Test that nested default factories work correctly."""
        config = InferenceEngineConfig()

        # Each default should be a fresh instance
        config2 = InferenceEngineConfig()

        # They should be equal but not the same object
        assert (
            config.controller_config.replica_controller_config.model_deployment_config.model
            == config2.controller_config.replica_controller_config.model_deployment_config.model
        )


class TestComputedFields:
    """Test computed fields set in __post_init__ (vajra pattern)."""

    def test_parallelism_computed_total(self):
        """Test computed total_gpus field."""
        config = ParallelismConfig(
            tensor_parallel=4, pipeline_parallel=2, data_parallel=8
        )
        assert config.total_gpus == 64
        assert config.world_size == 64

    def test_parallelism_verify_method(self):
        """Test method using computed fields."""
        config = ParallelismConfig(tensor_parallel=4, pipeline_parallel=2)
        assert config.verify_parallelism(available_gpus=8)
        assert not config.verify_parallelism(available_gpus=4)

    def test_memory_conditional_field(self):
        """Test conditional field modification in __post_init__."""
        # Auto-detect (None -> 64)
        config = MemoryConfig(cpu_memory_gb=None)
        assert config.effective_cpu_memory_gb == 64
        assert config.total_memory_gb == 64

        # Explicit value
        config = MemoryConfig(cpu_memory_gb=32, swap_space_gb=16)
        assert config.effective_cpu_memory_gb == 32
        assert config.total_memory_gb == 48

    def test_training_effective_batch_size(self):
        """Test effective batch size computed from nested configs."""
        config = TrainingConfig(
            batch=BatchConfig(max_batch_size=32),
            parallelism=ParallelismConfig(data_parallel=4),
            gradient_accumulation_steps=2,
        )
        # 32 * 4 * 2 = 256
        assert config.effective_batch_size == 256

    def test_multi_model_total_world_size(self):
        """Test computed property across list of configs."""
        config = MultiModelConfig(
            models=[
                ModelDeploymentConfig(tensor_parallel_size=4),
                ModelDeploymentConfig(tensor_parallel_size=2, pipeline_parallel_size=2),
            ]
        )
        # 4*1 + 2*2 = 8
        assert config.total_world_size == 8
        assert config.default_model.tensor_parallel_size == 4


class TestCrossFieldValidation:
    """Test cross-field validation (vajra pattern)."""

    def test_dynamic_chunk_min_max_validation(self):
        """Test min < max validation."""
        # Valid
        config = DynamicChunkComputeManagerConfig(
            min_chunk_size=512, max_chunk_size=4096
        )
        assert config.min_chunk_size < config.max_chunk_size

        # Invalid: min >= max
        with pytest.raises(ValueError, match="min_chunk_size must be less than"):
            DynamicChunkComputeManagerConfig(min_chunk_size=4096, max_chunk_size=512)

        with pytest.raises(ValueError, match="min_chunk_size must be less than"):
            DynamicChunkComputeManagerConfig(min_chunk_size=1000, max_chunk_size=1000)

    def test_cache_tier_watermark_validation(self):
        """Test admission < demotion validation."""
        # Valid
        config = CacheTierConfig(admission_watermark=0.05, demotion_watermark=0.1)
        assert config.admission_watermark < config.demotion_watermark

        # Invalid: admission >= demotion
        with pytest.raises(ValueError, match="admission_watermark must be less than"):
            CacheTierConfig(admission_watermark=0.2, demotion_watermark=0.1)

    def test_batch_divisibility_validation(self):
        """Test divisibility validation."""
        # Valid: range 63 is divisible by step 1
        config = BatchConfig(min_batch_size=1, max_batch_size=64, batch_size_step=1)
        assert config.min_batch_size == 1

        # Valid: range 56 is divisible by step 8
        config = BatchConfig(min_batch_size=8, max_batch_size=64, batch_size_step=8)
        assert config.batch_size_step == 8

        # Invalid: range 60 is not divisible by step 8
        with pytest.raises(ValueError, match="divisible by step"):
            BatchConfig(min_batch_size=4, max_batch_size=64, batch_size_step=8)

    def test_batch_min_max_validation(self):
        """Test min <= max validation."""
        with pytest.raises(ValueError, match="min_batch_size must be <="):
            BatchConfig(min_batch_size=100, max_batch_size=50)


class TestFilePathTemplates:
    """Test file path template patterns (vajra pattern)."""

    def test_computed_paths(self):
        """Test computed directory paths."""
        config = FilePathConfig(
            base_dir="/models", model_name="llama-7b", checkpoint_subdir="ckpt"
        )
        assert config.checkpoint_dir == "/models/llama-7b/ckpt"
        assert config.log_dir == "/models/llama-7b/logs"

    def test_path_methods(self):
        """Test path generation methods."""
        config = FilePathConfig(base_dir="/data", model_name="gpt")
        assert config.get_checkpoint_path(100) == "/data/gpt/checkpoints/step_100.pt"
        assert config.get_log_path("train") == "/data/gpt/logs/train.log"

    def test_training_config_path_delegation(self):
        """Test path method delegation in nested config."""
        config = TrainingConfig(
            paths=FilePathConfig(base_dir="/experiments", model_name="test")
        )
        assert (
            config.get_checkpoint_path(50) == "/experiments/test/checkpoints/step_50.pt"
        )


class TestSchedulerHierarchy:
    """Test scheduler polymorphic hierarchy."""

    def test_all_scheduler_types(self):
        """Test all scheduler type variants."""
        for sched_type in SchedulerType:
            config = AbstractSchedulerConfig.create_from_type(sched_type)
            assert config.get_type() == sched_type

    def test_scheduler_from_dict(self):
        """Test creating schedulers from dict."""
        config = create_class_from_dict(
            AbstractSchedulerConfig,
            {
                "type": "balanced",
                "balance_interval_ms": 200,
                "max_imbalance_ratio": 0.1,
            },
        )
        assert isinstance(config, BalancedSchedulerConfig)
        assert config.balance_interval_ms == 200

    def test_scheduler_validation(self):
        """Test scheduler-specific validation."""
        with pytest.raises(ValueError, match="balance_interval_ms must be positive"):
            BalancedSchedulerConfig(balance_interval_ms=0)

        with pytest.raises(ValueError, match="num_priority_levels must be at least 1"):
            PrioritySchedulerConfig(num_priority_levels=0)


class TestStorageBackendHierarchy:
    """Test storage backend polymorphic hierarchy."""

    def test_all_storage_types(self):
        """Test all storage backend type variants."""
        for storage_type in StorageBackendType:
            config = AbstractStorageBackendConfig.create_from_type(storage_type)
            assert config.get_type() == storage_type

    def test_local_storage_path_method(self):
        """Test local storage path method."""
        config = LocalStorageConfig(root_path="/data/store")
        assert config.get_full_path("models/v1") == "/data/store/models/v1"

    def test_s3_storage_key_method(self):
        """Test S3 storage key method."""
        config = S3StorageConfig(bucket="my-bucket", prefix="training/run1")
        assert config.get_full_key("checkpoint.pt") == "training/run1/checkpoint.pt"

        config_no_prefix = S3StorageConfig(bucket="my-bucket", prefix="")
        assert config_no_prefix.get_full_key("checkpoint.pt") == "checkpoint.pt"

    def test_storage_from_dict(self):
        """Test creating storage configs from dict."""
        config = create_class_from_dict(
            AbstractStorageBackendConfig,
            {"type": "s3", "bucket": "test-bucket", "region": "eu-west-1"},
        )
        assert isinstance(config, S3StorageConfig)
        assert config.bucket == "test-bucket"
        assert config.region == "eu-west-1"


class TestTrainingConfigIntegration:
    """Integration tests for complex TrainingConfig."""

    def test_default_instantiation(self):
        """Test TrainingConfig with all defaults."""
        config = TrainingConfig()
        assert config.parallelism.total_gpus == 1
        assert config.effective_batch_size == 64  # 64 * 1 * 1
        assert isinstance(config.scheduler, GreedySchedulerConfig)
        assert isinstance(config.storage, LocalStorageConfig)

    def test_full_config_from_dict(self):
        """Test creating full TrainingConfig from dict."""
        config_dict = {
            "parallelism": {
                "tensor_parallel": 4,
                "pipeline_parallel": 2,
                "data_parallel": 2,
            },
            "batch": {"min_batch_size": 8, "max_batch_size": 32, "batch_size_step": 8},
            "memory": {"gpu_memory_fraction": 0.95, "cpu_memory_gb": 128},
            "paths": {"base_dir": "/experiments", "model_name": "my-model"},
            "scheduler": {
                "type": "priority",
                "num_priority_levels": 5,
                "preemption_enabled": True,
            },
            "storage": {"type": "s3", "bucket": "training-data", "prefix": "run123"},
            "learning_rate": 0.0001,
            "num_epochs": 100,
            "gradient_accumulation_steps": 4,
        }
        config = create_class_from_dict(TrainingConfig, config_dict)

        # Verify nested configs
        assert config.parallelism.total_gpus == 16  # 4*2*2
        assert config.parallelism.verify_parallelism(16)
        assert not config.parallelism.verify_parallelism(8)

        # Verify computed fields
        # effective_batch = 32 * 2 * 4 = 256
        assert config.effective_batch_size == 256

        # Verify polymorphic configs
        assert isinstance(config.scheduler, PrioritySchedulerConfig)
        assert config.scheduler.num_priority_levels == 5
        assert isinstance(config.storage, S3StorageConfig)
        assert config.storage.bucket == "training-data"

        # Verify path methods
        assert config.paths.checkpoint_dir == "/experiments/my-model/checkpoints"

    def test_roundtrip_serialization(self):
        """Test TrainingConfig roundtrip through dict."""
        original = TrainingConfig(
            parallelism=ParallelismConfig(tensor_parallel=8),
            scheduler=PrioritySchedulerConfig(num_priority_levels=4),
            storage=S3StorageConfig(bucket="test"),
            learning_rate=0.001,
        )
        as_dict = dataclass_to_dict(original)
        reconstructed = create_class_from_dict(TrainingConfig, as_dict)

        assert reconstructed.parallelism.tensor_parallel == 8
        assert reconstructed.parallelism.total_gpus == 8
        assert isinstance(reconstructed.scheduler, PrioritySchedulerConfig)
        assert reconstructed.learning_rate == 0.001

    def test_validate_resources_method(self):
        """Test resource validation method."""
        config = TrainingConfig(
            parallelism=ParallelismConfig(tensor_parallel=4, data_parallel=2)
        )
        assert config.validate_resources(available_gpus=8)
        assert not config.validate_resources(available_gpus=4)


class TestMultiModelConfig:
    """Test config with list of polymorphic configs."""

    def test_empty_models_list(self):
        """Test MultiModelConfig with empty models."""
        config = MultiModelConfig(models=[])
        assert config.default_model is None
        assert config.total_world_size == 0

    def test_models_list_from_dict(self):
        """Test creating MultiModelConfig with models from dict."""
        config_dict = {
            "models": [
                {"type": "llm", "model": "llama-7b", "tensor_parallel_size": 2},
                {"type": "llm", "model": "llama-13b", "tensor_parallel_size": 4},
            ],
            "default_model_index": 1,
        }
        config = create_class_from_dict(MultiModelConfig, config_dict)

        assert len(config.models) == 2
        assert config.models[0].model == "llama-7b"
        assert config.models[1].model == "llama-13b"
        assert config.default_model.model == "llama-13b"
        assert config.total_world_size == 6  # 2 + 4

    def test_invalid_default_index(self):
        """Test validation of default_model_index."""
        with pytest.raises(ValueError, match="default_model_index .* out of range"):
            MultiModelConfig(
                models=[ModelDeploymentConfig()],
                default_model_index=5,
            )


class TestPositiveValidation:
    """Test positive value validation across configs."""

    def test_parallelism_positive(self):
        """Test parallelism values must be positive."""
        with pytest.raises(ValueError, match="tensor_parallel must be positive"):
            ParallelismConfig(tensor_parallel=0)

        with pytest.raises(ValueError, match="pipeline_parallel must be positive"):
            ParallelismConfig(pipeline_parallel=-1)

    def test_batch_positive(self):
        """Test batch values must be positive."""
        with pytest.raises(ValueError, match="min_batch_size must be positive"):
            BatchConfig(min_batch_size=0)

        with pytest.raises(ValueError, match="batch_size_step must be positive"):
            BatchConfig(batch_size_step=0)

    def test_memory_validation(self):
        """Test memory config validation."""
        with pytest.raises(ValueError, match="gpu_memory_fraction must be in"):
            MemoryConfig(gpu_memory_fraction=0)

        with pytest.raises(ValueError, match="gpu_memory_fraction must be in"):
            MemoryConfig(gpu_memory_fraction=1.5)

        with pytest.raises(ValueError, match="swap_space_gb must be non-negative"):
            MemoryConfig(swap_space_gb=-1)

    def test_training_positive(self):
        """Test training config positive validation."""
        with pytest.raises(ValueError, match="learning_rate must be positive"):
            TrainingConfig(learning_rate=0)

        with pytest.raises(ValueError, match="num_epochs must be positive"):
            TrainingConfig(num_epochs=0)


class TestFlatDataclassForNewConfigs:
    """Test flat dataclass creation for new config types."""

    def test_training_config_flat(self):
        """Test flat dataclass for TrainingConfig."""
        FlatConfig = create_flat_dataclass(TrainingConfig)
        field_names = [f.name for f in FlatConfig.__dataclass_fields__.values()]

        # Should have nested fields with prefixes
        assert any("parallelism" in name for name in field_names)
        assert any("batch" in name for name in field_names)
        assert any("scheduler" in name for name in field_names)

    def test_multi_model_flat(self):
        """Test flat dataclass for MultiModelConfig."""
        FlatConfig = create_flat_dataclass(MultiModelConfig)
        assert FlatConfig is not None


# =============================================================================
# CLI Argument Parsing Tests (vajra pattern)
# =============================================================================
import tempfile

import yaml

from vidhi import load_yaml_config


class TestCLIArgumentParsing:
    """Test CLI argument parsing for configs."""

    def test_flat_dataclass_field_names(self):
        """Test that flat dataclass has correct field names with separators."""
        FlatConfig = create_flat_dataclass(CacheConfig)
        field_names = [f.name for f in FlatConfig.__dataclass_fields__.values()]

        # Nested fields use __ separator internally (. in CLI args)
        assert "allocator_type" in field_names  # type field for polymorphic
        assert "gpu_tier__admission_watermark" in field_names
        assert "gpu_tier__demotion_watermark" in field_names

    def test_flat_dataclass_deep_nesting(self):
        """Test flat dataclass for deeply nested configs."""
        FlatConfig = create_flat_dataclass(InferenceEngineConfig)
        field_names = [f.name for f in FlatConfig.__dataclass_fields__.values()]

        # Should have nested polymorphic config fields
        assert any("controller_config" in name for name in field_names)
        # Deeply nested polymorphic fields are kept as composite references
        assert any("replica_controller_config" in name for name in field_names)

    def test_flat_dataclass_polymorphic_type_field(self):
        """Test that polymorphic configs get type fields."""
        FlatConfig = create_flat_dataclass(CacheConfig)
        field_names = [f.name for f in FlatConfig.__dataclass_fields__.values()]

        # Polymorphic allocator should have a type field
        assert "allocator_type" in field_names

    def test_flat_dataclass_has_all_nested_fields(self):
        """Test that flat config has all fields from nested structure."""
        FlatConfig = create_flat_dataclass(CacheConfig)
        field_names = set(f.name for f in FlatConfig.__dataclass_fields__.values())

        # Should have top-level fields
        assert "page_size" in field_names
        assert "max_promotion_batch_size" in field_names
        assert "enable_prefix_caching" in field_names

        # Should have nested tier fields
        assert "gpu_tier__admission_watermark" in field_names
        assert "gpu_tier__demotion_watermark" in field_names
        assert "cpu_tier__admission_watermark" in field_names
        assert "nvme_tier__demotion_watermark" in field_names

        # Should have polymorphic type field
        assert "allocator_type" in field_names

        # Should have variant-specific fields
        assert any("decay_rate" in name for name in field_names)
        assert any("use_frequency" in name for name in field_names)

    def test_cli_help_text_propagation(self):
        """Test that help text from field() is preserved in flat dataclass."""
        FlatConfig = create_flat_dataclass(CacheConfig)

        # Check that help text is in metadata
        assert "help" in FlatConfig.metadata_mapping["page_size"]
        assert "Cache page size" in FlatConfig.metadata_mapping["page_size"]["help"]

    def test_flat_dataclass_with_training_config(self):
        """Test flat dataclass for complex TrainingConfig."""
        FlatConfig = create_flat_dataclass(TrainingConfig)
        field_names = set(f.name for f in FlatConfig.__dataclass_fields__.values())

        # Check various nested fields exist (using __ separator)
        assert "learning_rate" in field_names
        assert "num_epochs" in field_names
        assert "parallelism__tensor_parallel" in field_names
        assert "parallelism__pipeline_parallel" in field_names
        assert "batch__min_batch_size" in field_names
        assert "batch__max_batch_size" in field_names
        assert "scheduler_type" in field_names
        assert "storage_type" in field_names


class TestFileBasedConfigLoading:
    """Test YAML/JSON file-based config loading (vajra pattern)."""

    def test_load_yaml_simple(self):
        """Test loading simple YAML config."""
        yaml_content = """
page_size: 64
enable_prefix_caching: false
allocator:
  type: lfu
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            yaml_path = f.name

        try:
            config_dict = load_yaml_config(yaml_path)
            config = create_class_from_dict(CacheConfig, config_dict)

            assert config.page_size == 64
            assert config.enable_prefix_caching is False
            assert isinstance(config.allocator, LfuAllocatorConfig)
        finally:
            import os

            os.unlink(yaml_path)

    def test_load_yaml_nested(self):
        """Test loading nested YAML config."""
        yaml_content = """
controller_config:
  type: llm
  replica_controller_config:
    type: llm_base
    model_deployment_config:
      type: llm
      model: "gpt-4"
      tensor_parallel_size: 8
    cache_config:
      page_size: 128
      allocator:
        type: cost_aware_exp_decay
        decay_rate: 0.7
metrics_config:
  enable_metrics: true
  metrics_port: 8080
resource_allocator_config:
  type: ray
  ray_address: "ray://cluster:10001"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            yaml_path = f.name

        try:
            config_dict = load_yaml_config(yaml_path)
            config = create_class_from_dict(InferenceEngineConfig, config_dict)

            # Verify deep nesting
            assert (
                config.controller_config.replica_controller_config.model_deployment_config.model
                == "gpt-4"
            )
            assert (
                config.controller_config.replica_controller_config.model_deployment_config.tensor_parallel_size
                == 8
            )
            assert (
                config.controller_config.replica_controller_config.cache_config.page_size
                == 128
            )
            assert isinstance(
                config.controller_config.replica_controller_config.cache_config.allocator,
                CostAwareExpDecayAllocatorConfig,
            )
            assert config.metrics_config.metrics_port == 8080
            assert isinstance(
                config.resource_allocator_config, RayGpuResourceAllocatorConfig
            )
        finally:
            import os

            os.unlink(yaml_path)

    def test_load_yaml_with_training_config(self):
        """Test loading complex TrainingConfig from YAML."""
        yaml_content = """
parallelism:
  tensor_parallel: 4
  pipeline_parallel: 2
  data_parallel: 2
batch:
  min_batch_size: 8
  max_batch_size: 64
  batch_size_step: 8
memory:
  gpu_memory_fraction: 0.95
  cpu_memory_gb: 256
paths:
  base_dir: "/experiments"
  model_name: "llama-70b"
scheduler:
  type: priority
  num_priority_levels: 5
storage:
  type: s3
  bucket: "ml-training"
  prefix: "checkpoints"
learning_rate: 0.0001
num_epochs: 50
gradient_accumulation_steps: 8
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            yaml_path = f.name

        try:
            config_dict = load_yaml_config(yaml_path)
            config = create_class_from_dict(TrainingConfig, config_dict)

            # Verify all nested values
            assert config.parallelism.tensor_parallel == 4
            assert config.parallelism.total_gpus == 16  # 4*2*2
            assert config.batch.max_batch_size == 64
            assert config.memory.effective_cpu_memory_gb == 256
            assert config.paths.checkpoint_dir == "/experiments/llama-70b/checkpoints"
            assert isinstance(config.scheduler, PrioritySchedulerConfig)
            assert config.scheduler.num_priority_levels == 5
            assert isinstance(config.storage, S3StorageConfig)
            assert config.storage.bucket == "ml-training"
            # Verify computed field
            # effective_batch = 64 * 2 * 8 = 1024
            assert config.effective_batch_size == 1024
        finally:
            import os

            os.unlink(yaml_path)

    def test_load_json_config(self):
        """Test loading JSON config file."""
        json_content = '{"page_size": 32, "allocator": {"type": "lru"}}'

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write(json_content)
            json_path = f.name

        try:
            config_dict = load_yaml_config(json_path)  # YAML loader handles JSON too
            config = create_class_from_dict(CacheConfig, config_dict)

            assert config.page_size == 32
            assert isinstance(config.allocator, LruAllocatorConfig)
        finally:
            import os

            os.unlink(json_path)


class TestConfigRoundtrip:
    """Test config serialization roundtrip (vajra pattern: save -> load -> verify)."""

    def test_simple_config_roundtrip(self):
        """Test simple config YAML roundtrip."""
        original = CacheConfig(
            page_size=64,
            allocator=CostAwareGdsfAllocatorConfig(
                prefill_profiling_path="/custom/path.json"
            ),
            enable_prefix_caching=False,
        )

        # Serialize to dict
        as_dict = dataclass_to_dict(original)

        # Save to YAML
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(as_dict, f)
            yaml_path = f.name

        try:
            # Load back
            loaded_dict = load_yaml_config(yaml_path)
            reconstructed = create_class_from_dict(CacheConfig, loaded_dict)

            # Verify
            assert reconstructed.page_size == original.page_size
            assert reconstructed.enable_prefix_caching == original.enable_prefix_caching
            assert isinstance(reconstructed.allocator, CostAwareGdsfAllocatorConfig)
            assert (
                reconstructed.allocator.prefill_profiling_path
                == original.allocator.prefill_profiling_path
            )
        finally:
            import os

            os.unlink(yaml_path)

    def test_complex_config_roundtrip(self):
        """Test complex nested config YAML roundtrip."""
        original = InferenceEngineConfig(
            controller_config=ReplicasetControllerConfig(
                replica_controller_config=ReplicaControllerConfig(
                    model_deployment_config=ModelDeploymentConfig(
                        model="test-model",
                        tensor_parallel_size=4,
                    ),
                    cache_config=CacheConfig(
                        page_size=64,
                        allocator=CostAwareExpDecayAllocatorConfig(decay_rate=0.8),
                    ),
                ),
                session_prioritizer_config=EdfSessionPrioritizerConfig(
                    default_deadline_ms=500.0
                ),
            ),
            resource_allocator_config=MockResourceAllocatorConfig(num_mock_gpus=16),
        )

        # Serialize
        as_dict = dataclass_to_dict(original)

        # Save and load
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(as_dict, f)
            yaml_path = f.name

        try:
            loaded_dict = load_yaml_config(yaml_path)
            reconstructed = create_class_from_dict(InferenceEngineConfig, loaded_dict)

            # Deep verification
            orig_model = (
                original.controller_config.replica_controller_config.model_deployment_config
            )
            recon_model = (
                reconstructed.controller_config.replica_controller_config.model_deployment_config
            )
            assert recon_model.model == orig_model.model
            assert recon_model.tensor_parallel_size == orig_model.tensor_parallel_size

            orig_cache = (
                original.controller_config.replica_controller_config.cache_config
            )
            recon_cache = (
                reconstructed.controller_config.replica_controller_config.cache_config
            )
            assert recon_cache.page_size == orig_cache.page_size
            assert isinstance(recon_cache.allocator, CostAwareExpDecayAllocatorConfig)
            assert recon_cache.allocator.decay_rate == 0.8

            assert isinstance(
                reconstructed.controller_config.session_prioritizer_config,
                EdfSessionPrioritizerConfig,
            )
            assert isinstance(
                reconstructed.resource_allocator_config, MockResourceAllocatorConfig
            )
        finally:
            import os

            os.unlink(yaml_path)

    def test_training_config_roundtrip(self):
        """Test TrainingConfig YAML roundtrip with computed fields."""
        original = TrainingConfig(
            parallelism=ParallelismConfig(tensor_parallel=8, data_parallel=4),
            batch=BatchConfig(min_batch_size=16, max_batch_size=64, batch_size_step=16),
            scheduler=BalancedSchedulerConfig(balance_interval_ms=50),
            storage=GCSStorageConfig(bucket="test-bucket", project="my-project"),
            learning_rate=0.0005,
            gradient_accumulation_steps=4,
        )

        # Verify original computed fields
        assert original.parallelism.total_gpus == 32
        assert original.effective_batch_size == 64 * 4 * 4  # 1024

        # Roundtrip
        as_dict = dataclass_to_dict(original)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(as_dict, f)
            yaml_path = f.name

        try:
            loaded_dict = load_yaml_config(yaml_path)
            reconstructed = create_class_from_dict(TrainingConfig, loaded_dict)

            # Verify values preserved
            assert reconstructed.parallelism.tensor_parallel == 8
            assert reconstructed.parallelism.data_parallel == 4
            assert reconstructed.learning_rate == 0.0005

            # Verify computed fields recomputed correctly
            assert reconstructed.parallelism.total_gpus == 32
            assert reconstructed.effective_batch_size == 1024

            # Verify polymorphic types
            assert isinstance(reconstructed.scheduler, BalancedSchedulerConfig)
            assert reconstructed.scheduler.balance_interval_ms == 50
            assert isinstance(reconstructed.storage, GCSStorageConfig)
            assert reconstructed.storage.project == "my-project"
        finally:
            import os

            os.unlink(yaml_path)


class TestConfigFileLoading:
    """Test --config flag for loading configs from files."""

    def test_config_file_loading(self):
        """Test that --config flag loads config from YAML file."""
        import sys
        import tempfile
        from pathlib import Path
        from unittest.mock import patch

        @frozen_dataclass
        class FileLoadableConfig:
            value: int = field(10, help="A value")
            name: str = field("default", help="A name")

        yaml_content = """
value: 42
name: "from_file"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            yaml_path = f.name

        try:
            FlatConfig = create_flat_dataclass(FileLoadableConfig)
            test_args = ["script.py", "--config", yaml_path]

            with patch.object(sys, "argv", test_args):
                configs = FlatConfig.create_from_cli_args()

            config = configs[0].reconstruct_original_dataclass()
            assert config.value == 42
            assert config.name == "from_file"
        finally:
            Path(yaml_path).unlink()

    def test_config_file_with_nested_configs(self):
        """Test --config with nested configs."""
        import sys
        import tempfile
        from pathlib import Path
        from unittest.mock import patch

        @frozen_dataclass
        class InnerConfig:
            inner_val: int = 5

        @frozen_dataclass
        class OuterConfig:
            inner: InnerConfig = dataclass_field(default_factory=InnerConfig)
            outer_val: str = "outer"

        yaml_content = """
outer_val: "from_config"
inner:
  inner_val: 99
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            yaml_path = f.name

        try:
            FlatConfig = create_flat_dataclass(OuterConfig)
            test_args = ["script.py", "--config", yaml_path]

            with patch.object(sys, "argv", test_args):
                configs = FlatConfig.create_from_cli_args()

            config = configs[0].reconstruct_original_dataclass()
            assert config.outer_val == "from_config"
            assert config.inner.inner_val == 99
        finally:
            Path(yaml_path).unlink()


class TestPolymorphicCLI:
    """Test polymorphic config handling in CLI."""

    def test_polymorphic_type_field_in_flat(self):
        """Test that polymorphic configs have type fields in flat dataclass."""

        @frozen_dataclass
        class ConfigWithPoly:
            allocator: AbstractAllocatorConfig = dataclass_field(
                default_factory=LruAllocatorConfig
            )
            name: str = "test"

        FlatConfig = create_flat_dataclass(ConfigWithPoly)
        field_names = [f.name for f in FlatConfig.__dataclass_fields__.values()]

        # Type field uses _type suffix
        assert "allocator_type" in field_names

    def test_polymorphic_variant_fields_tracked(self):
        """Test that polymorphic variant fields are tracked separately."""

        @frozen_dataclass
        class ConfigWithPoly:
            allocator: AbstractAllocatorConfig = dataclass_field(
                default_factory=LruAllocatorConfig
            )

        FlatConfig = create_flat_dataclass(ConfigWithPoly)

        # Variant-specific fields should be tracked
        assert hasattr(FlatConfig, "poly_variant_fields")
        # Fields like decay_rate (only for cost_aware_exp_decay) should be variant fields
        assert any(
            "decay_rate" in field_name for field_name in FlatConfig.poly_variant_fields
        )

    def test_all_polymorphic_variants_have_fields(self):
        """Test that all polymorphic variant fields are present."""

        @frozen_dataclass
        class ConfigWithPoly:
            allocator: AbstractAllocatorConfig = dataclass_field(
                default_factory=LruAllocatorConfig
            )

        FlatConfig = create_flat_dataclass(ConfigWithPoly)
        field_names = set(f.name for f in FlatConfig.__dataclass_fields__.values())

        # Should have fields for all allocator variants (using __ separator and variant prefix)
        # CostAwareExpDecayAllocatorConfig fields
        assert any("decay_rate" in name for name in field_names)
        assert any("min_cost" in name for name in field_names)
        assert any("prefill_profiling_path" in name for name in field_names)

        # CostAwareGdsfAllocatorConfig fields
        assert any("use_frequency" in name for name in field_names)


class TestEnumHandling:
    """Test enum handling in CLI and serialization."""

    def test_enum_serialization(self):
        """Test that enums serialize to their values."""
        # Use allocator config which has enum type
        config = LruAllocatorConfig()
        as_dict = dataclass_to_dict(config)

        # Type should be the enum VALUE, not name
        assert as_dict["type"] == "lru"  # Not "LRU"

    def test_enum_deserialization_from_value(self):
        """Test that enums can be deserialized from string values."""
        config_dict = {"type": "cost_aware_gdsf", "use_frequency": False}
        config = create_class_from_dict(AbstractAllocatorConfig, config_dict)

        assert isinstance(config, CostAwareGdsfAllocatorConfig)
        assert config.use_frequency is False

    def test_enum_deserialization_case_insensitive(self):
        """Test case-insensitive enum deserialization."""
        # Uppercase
        config = AbstractAllocatorConfig.create_from_type("LRU")
        assert isinstance(config, LruAllocatorConfig)

        # Lowercase
        config = AbstractAllocatorConfig.create_from_type("lru")
        assert isinstance(config, LruAllocatorConfig)

        # Mixed case
        config = AbstractAllocatorConfig.create_from_type("Lru")
        assert isinstance(config, LruAllocatorConfig)

    def test_scheduler_enum_roundtrip(self):
        """Test scheduler enum serialization roundtrip."""
        original = TrainingConfig(
            scheduler=PrioritySchedulerConfig(num_priority_levels=7)
        )

        as_dict = dataclass_to_dict(original)

        # Verify enum value in dict
        assert as_dict["scheduler"]["type"] == "priority"

        # Roundtrip
        reconstructed = create_class_from_dict(TrainingConfig, as_dict)
        assert isinstance(reconstructed.scheduler, PrioritySchedulerConfig)
        assert reconstructed.scheduler.num_priority_levels == 7


class TestListFieldHandling:
    """Test list field handling in configs."""

    def test_list_of_primitives(self):
        """Test list of primitive values."""

        @frozen_dataclass
        class ConfigWithList:
            values: List[int] = dataclass_field(default_factory=list)
            name: str = "test"

        config = ConfigWithList(values=[1, 2, 3, 4, 5])
        as_dict = dataclass_to_dict(config)

        assert as_dict["values"] == [1, 2, 3, 4, 5]

        reconstructed = create_class_from_dict(ConfigWithList, as_dict)
        assert reconstructed.values == [1, 2, 3, 4, 5]

    def test_list_of_dataclasses(self):
        """Test list of dataclass values."""
        config = MultiModelConfig(
            models=[
                ModelDeploymentConfig(model="model-a", tensor_parallel_size=2),
                ModelDeploymentConfig(model="model-b", tensor_parallel_size=4),
            ]
        )

        as_dict = dataclass_to_dict(config)

        assert len(as_dict["models"]) == 2
        assert as_dict["models"][0]["model"] == "model-a"

        reconstructed = create_class_from_dict(MultiModelConfig, as_dict)
        assert len(reconstructed.models) == 2
        assert reconstructed.models[0].model == "model-a"
        assert reconstructed.models[1].tensor_parallel_size == 4

    def test_list_field_in_flat_dataclass(self):
        """Test that list fields are tracked in flat dataclass."""
        FlatConfig = create_flat_dataclass(MultiModelConfig)

        assert hasattr(FlatConfig, "list_fields")


class TestOptionalFieldHandling:
    """Test Optional field handling."""

    def test_optional_none_value(self):
        """Test Optional field with None value."""
        config = MemoryConfig(cpu_memory_gb=None)

        as_dict = dataclass_to_dict(config)
        # None should be serialized
        assert as_dict["cpu_memory_gb"] is None

        reconstructed = create_class_from_dict(MemoryConfig, as_dict)
        assert reconstructed.cpu_memory_gb is None
        # But effective memory should be auto-detected
        assert reconstructed.effective_cpu_memory_gb == 64

    def test_optional_with_value(self):
        """Test Optional field with actual value."""
        config = MemoryConfig(cpu_memory_gb=128)

        as_dict = dataclass_to_dict(config)
        assert as_dict["cpu_memory_gb"] == 128

        reconstructed = create_class_from_dict(MemoryConfig, as_dict)
        assert reconstructed.cpu_memory_gb == 128
        assert reconstructed.effective_cpu_memory_gb == 128

    def test_optional_in_storage_config(self):
        """Test Optional fields in storage configs."""
        # S3 with optional endpoint
        config = S3StorageConfig(bucket="test", endpoint_url="http://localhost:9000")
        as_dict = dataclass_to_dict(config)
        assert as_dict["endpoint_url"] == "http://localhost:9000"

        # S3 without optional endpoint
        config = S3StorageConfig(bucket="test", endpoint_url=None)
        as_dict = dataclass_to_dict(config)
        assert as_dict["endpoint_url"] is None
