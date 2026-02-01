"""
Main Rotavision client.
"""

from typing import Optional

from rotavision.vishwas import Vishwas
from rotavision.guardian import Guardian
from rotavision.dastavez import Dastavez
from rotavision.sankalp import Sankalp
from rotavision.orchestrate import Orchestrate
from rotavision.gati import Gati


class Rotavision:
    """
    Main client for Rotavision AI Trust Infrastructure.

    Usage:
        from rotavision import Rotavision

        client = Rotavision(api_key="rv_...")

        # Use product-specific clients
        result = client.vishwas.analyze(text="...")
        result = client.guardian.monitor(prompt="...", response="...")
    """

    BASE_URL = "https://api.rotavision.com"

    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        timeout: float = 30.0,
    ):
        """
        Initialize the Rotavision client.

        Args:
            api_key: Your Rotavision API key (rv_live_... or rv_test_...)
            base_url: Optional custom API base URL
            timeout: Request timeout in seconds (default: 30)
        """
        self.api_key = api_key
        self.base_url = base_url or self.BASE_URL
        self.timeout = timeout

        # Initialize product clients
        self._vishwas: Optional[Vishwas] = None
        self._guardian: Optional[Guardian] = None
        self._dastavez: Optional[Dastavez] = None
        self._sankalp: Optional[Sankalp] = None
        self._orchestrate: Optional[Orchestrate] = None
        self._gati: Optional[Gati] = None

    @property
    def vishwas(self) -> Vishwas:
        """Trust, Fairness & Explainability API."""
        if self._vishwas is None:
            self._vishwas = Vishwas(self)
        return self._vishwas

    @property
    def guardian(self) -> Guardian:
        """AI Reliability Monitoring API."""
        if self._guardian is None:
            self._guardian = Guardian(self)
        return self._guardian

    @property
    def dastavez(self) -> Dastavez:
        """Document AI + Browser Agents API."""
        if self._dastavez is None:
            self._dastavez = Dastavez(self)
        return self._dastavez

    @property
    def sankalp(self) -> Sankalp:
        """Sovereign AI Gateway API."""
        if self._sankalp is None:
            self._sankalp = Sankalp(self)
        return self._sankalp

    @property
    def orchestrate(self) -> Orchestrate:
        """Multi-Agent Platform API."""
        if self._orchestrate is None:
            self._orchestrate = Orchestrate(self)
        return self._orchestrate

    @property
    def gati(self) -> Gati:
        """Fleet & Mobility Intelligence API."""
        if self._gati is None:
            self._gati = Gati(self)
        return self._gati
