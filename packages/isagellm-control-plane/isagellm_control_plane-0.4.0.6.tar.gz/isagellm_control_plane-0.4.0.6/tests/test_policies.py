"""Unit tests for scheduling policies."""

from __future__ import annotations

from sagellm_control.policies import (
    AdaptivePolicy,
    FIFOPolicy,
    PriorityPolicy,
    SLOAwarePolicy,
)
from sagellm_control.types import RequestMetadata, RequestPriority


class TestFIFOPolicy:
    """Tests for FIFO scheduling policy."""

    def test_create_fifo_policy(self):
        """Should create FIFO policy."""
        policy = FIFOPolicy()
        assert policy.name == "fifo"

    def test_fifo_ordering(self):
        """Should order requests by arrival time."""
        policy = FIFOPolicy()

        # Create requests with different arrival times
        req1 = RequestMetadata(request_id="req-001")
        req2 = RequestMetadata(request_id="req-002")
        req3 = RequestMetadata(request_id="req-003")

        # Add to policy
        policy.add_request(req1)
        policy.add_request(req2)
        policy.add_request(req3)

        # Should return in FIFO order
        assert policy.next_request().request_id == "req-001"
        assert policy.next_request().request_id == "req-002"
        assert policy.next_request().request_id == "req-003"

    def test_fifo_empty_queue(self):
        """Should return None for empty queue."""
        policy = FIFOPolicy()
        assert policy.next_request() is None


class TestPriorityPolicy:
    """Tests for Priority scheduling policy."""

    def test_create_priority_policy(self):
        """Should create Priority policy."""
        policy = PriorityPolicy()
        assert policy.name == "priority"

    def test_priority_ordering(self):
        """Should order requests by priority."""
        policy = PriorityPolicy()

        # Create requests with different priorities
        req_low = RequestMetadata(
            request_id="req-low",
            priority=RequestPriority.LOW,
        )
        req_critical = RequestMetadata(
            request_id="req-critical",
            priority=RequestPriority.CRITICAL,
        )
        req_normal = RequestMetadata(
            request_id="req-normal",
            priority=RequestPriority.NORMAL,
        )

        # Add in random order
        policy.add_request(req_low)
        policy.add_request(req_critical)
        policy.add_request(req_normal)

        # Should return in priority order (CRITICAL first)
        assert policy.next_request().request_id == "req-critical"
        assert policy.next_request().request_id == "req-normal"
        assert policy.next_request().request_id == "req-low"


class TestSLOAwarePolicy:
    """Tests for SLO-aware scheduling policy."""

    def test_create_slo_aware_policy(self):
        """Should create SLO-aware policy."""
        policy = SLOAwarePolicy()
        assert policy.name == "slo_aware"

    def test_slo_deadline_ordering(self):
        """Should prioritize requests with tighter deadlines."""
        policy = SLOAwarePolicy()

        # Create requests with different SLO deadlines
        req_tight = RequestMetadata(
            request_id="req-tight",
            slo_deadline_ms=100.0,
        )
        req_loose = RequestMetadata(
            request_id="req-loose",
            slo_deadline_ms=1000.0,
        )
        req_no_slo = RequestMetadata(
            request_id="req-no-slo",
            slo_deadline_ms=None,
        )

        # Add in random order
        policy.add_request(req_loose)
        policy.add_request(req_no_slo)
        policy.add_request(req_tight)

        # Should return tighter deadline first
        next_req = policy.next_request()
        assert next_req.request_id == "req-tight"


class TestAdaptivePolicy:
    """Tests for Adaptive scheduling policy."""

    def test_create_adaptive_policy(self):
        """Should create Adaptive policy."""
        policy = AdaptivePolicy()
        assert policy.name == "adaptive"

    def test_adaptive_combines_factors(self):
        """Should consider multiple factors."""
        policy = AdaptivePolicy()

        req = RequestMetadata(
            request_id="req-001",
            priority=RequestPriority.HIGH,
            slo_deadline_ms=200.0,
        )
        policy.add_request(req)

        next_req = policy.next_request()
        assert next_req is not None
        assert next_req.request_id == "req-001"
