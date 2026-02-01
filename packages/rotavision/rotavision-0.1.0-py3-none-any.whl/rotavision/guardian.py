"""
Guardian - AI Reliability Monitoring API.
"""

from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from rotavision.client import Rotavision


class Guardian:
    """
    Guardian API client for AI reliability monitoring.

    Usage:
        from rotavision import Rotavision

        client = Rotavision(api_key="rv_...")

        result = client.guardian.monitor(
            prompt="What is the RBI repo rate?",
            response="The RBI repo rate is 6.5%...",
            checks=["hallucination", "factuality"]
        )
    """

    def __init__(self, client: "Rotavision"):
        self._client = client

    def monitor(
        self,
        prompt: str,
        response: str,
        model: Optional[str] = None,
        checks: Optional[List[str]] = None,
        ground_truth: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Monitor AI model outputs for hallucination, drift, and sandbagging.

        Args:
            prompt: The input prompt
            response: The model's response
            model: Model identifier (e.g., "gpt-4")
            checks: Checks to run (hallucination, factuality, drift, sandbagging)
            ground_truth: Optional ground truth for factuality check
            session_id: Session identifier for tracking

        Returns:
            Monitoring result with check status and confidence scores
        """
        raise NotImplementedError("Coming soon. Contact developers@rotavision.com")

    def detect(
        self,
        model_endpoint: str,
        test_suite: str = "capability_probe",
        domains: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Detect capability sandbagging using activation probes.

        Args:
            model_endpoint: Your model's API endpoint
            test_suite: Test suite to run (capability_probe, safety_probe)
            domains: Capability domains to test (reasoning, math, coding)

        Returns:
            Detection results with capability scores and probe analysis
        """
        raise NotImplementedError("Coming soon. Contact developers@rotavision.com")

    def alerts(
        self,
        model_id: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 100,
    ) -> Dict[str, Any]:
        """
        Get monitoring alerts.

        Args:
            model_id: Filter by model identifier
            severity: Filter by severity (critical, warning, info)
            limit: Maximum number of alerts to return

        Returns:
            List of monitoring alerts
        """
        raise NotImplementedError("Coming soon. Contact developers@rotavision.com")
