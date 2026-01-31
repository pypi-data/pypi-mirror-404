"""
Integration module for connecting rotalabs-audit with other packages.

This module provides integration layers for connecting rotalabs-audit
with rotalabs-comply and other Rotalabs packages.
"""

from rotalabs_audit.integration.comply import ComplyIntegration, ReasoningAuditEntry

__all__ = [
    "ComplyIntegration",
    "ReasoningAuditEntry",
]
