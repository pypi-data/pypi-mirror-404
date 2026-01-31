"""sageLLM Control Plane - Intelligent request routing and scheduling.

The Control Plane sits between users and LLM execution instances, providing:
- Intelligent request routing and load balancing
- Advanced scheduling policies (priority, SLO-aware, cost-optimized)
- Engine lifecycle management (spawn, stop, health check)
- Performance monitoring and adaptive optimization

Quick Start:
    from sagellm_control import ControlPlaneManager
"""

from __future__ import annotations

__version__ = "0.4.0.6"

from sagellm_control.engine_client import (
    ClientConfig,
    EngineClient,
    EngineClientError,
    EngineRequestError,
    EngineTimeoutError,
    EngineUnavailableError,
    RequestContext,
    RetryPolicy,
)
from sagellm_control.lifecycle import EngineLifecycleManager
from sagellm_control.local_engine_client import LocalEngineClient
from sagellm_control.manager import ControlPlaneManager
from sagellm_control.policies import (
    AdaptivePolicy,
    FIFOPolicy,
    PriorityPolicy,
    SchedulingPolicy,
    SLOAwarePolicy,
)
from sagellm_control.router import LoadBalancer, RequestRouter
from sagellm_control.scaling import ScalingManager
from sagellm_control.types import (
    EngineInfo,
    EngineState,
    ExecutionInstanceType,
    RequestPriority,
    RequestStatus,
    RequestType,
    SchedulingDecision,
)

__all__ = [
    "__version__",
    # Types
    "EngineInfo",
    "EngineState",
    "RequestPriority",
    "RequestStatus",
    "RequestType",
    "SchedulingDecision",
    "ExecutionInstanceType",  # MVP: PD 分离支持
    # Manager
    "ControlPlaneManager",
    # Router
    "LoadBalancer",
    "RequestRouter",
    # Lifecycle
    "EngineLifecycleManager",
    # Scaling (MVP)
    "ScalingManager",
    # Policies
    "SchedulingPolicy",
    "FIFOPolicy",
    "PriorityPolicy",
    "SLOAwarePolicy",
    "AdaptivePolicy",
    # Engine Client
    "EngineClient",
    "LocalEngineClient",
    "ClientConfig",
    "RequestContext",
    "RetryPolicy",
    "EngineClientError",
    "EngineTimeoutError",
    "EngineUnavailableError",
    "EngineRequestError",
]
