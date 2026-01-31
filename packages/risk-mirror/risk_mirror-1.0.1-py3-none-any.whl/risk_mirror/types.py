"""
Risk Mirror SDK - Type Definitions
==================================
Dataclasses for SDK request/response models

US-0004: API Surface
US-0005: Data Model
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Literal
from enum import Enum


class Verdict(str, Enum):
    SAFE = "SAFE"
    REVIEW = "REVIEW"
    HIGH_RISK = "HIGH_RISK"


class Severity(str, Enum):
    LOW = "LOW"
    MED = "MED"
    HIGH = "HIGH"


@dataclass
class Finding:
    """A single finding from the scan."""
    category: str
    severity: Severity
    count: int
    match: Optional[str] = None


@dataclass
class AuditSummary:
    """Summary of modifications made."""
    phrases_removed: int = 0
    pii_redacted: int = 0
    secrets_masked: int = 0
    injections_blocked: int = 0


@dataclass
class ScanPolicy:
    """Configuration for scan behavior.
    
    US-0002: Policy Controls
    """
    pii: bool = True
    secrets: bool = True
    injection: bool = True
    pii_classes: Optional[List[str]] = None
    max_length: int = 100000


@dataclass
class Privacy:
    """Privacy guarantees."""
    stateless: bool = True
    content_logged: bool = False


@dataclass
class ScanResponse:
    """Response from scan operation.
    
    US-0009: Audit Evidence
    US-0010: Privacy
    US-0011: Compliance
    """
    verdict: Verdict
    findings: List[Finding]
    safe_output: str
    audit_summary: AuditSummary
    policy_hash: str
    engine_version: str
    latency_ms: float
    privacy: Optional[Privacy] = None
    compliance_tags: List[str] = field(default_factory=list)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScanResponse":
        """Create ScanResponse from API response dict."""
        findings = [
            Finding(
                category=f.get("category", "unknown"),
                severity=Severity(f.get("severity", "LOW")),
                count=f.get("count", 1),
                match=f.get("match"),
            )
            for f in data.get("findings", [])
        ]
        
        audit_data = data.get("audit_summary", {})
        audit_summary = AuditSummary(
            phrases_removed=audit_data.get("phrases_removed", 0),
            pii_redacted=audit_data.get("pii_redacted", 0),
            secrets_masked=audit_data.get("secrets_masked", 0),
            injections_blocked=audit_data.get("injections_blocked", 0),
        )
        
        privacy_data = data.get("privacy")
        privacy = Privacy(
            stateless=privacy_data.get("stateless", True),
            content_logged=privacy_data.get("content_logged", False),
        ) if privacy_data else Privacy()
        
        return cls(
            verdict=Verdict(data.get("verdict", "SAFE")),
            findings=findings,
            safe_output=data.get("safe_output", ""),
            audit_summary=audit_summary,
            policy_hash=data.get("policy_hash", ""),
            engine_version=data.get("engine_version", "6.0-ULTRA"),
            latency_ms=data.get("latency_ms", 0.0),
            privacy=privacy,
            compliance_tags=data.get("compliance_tags", []),
        )


@dataclass
class OptimizeResponse:
    """Response from optimize operation."""
    optimized: str
    tokens_saved: int
    compression_ratio: float
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OptimizeResponse":
        return cls(
            optimized=data.get("optimized", ""),
            tokens_saved=data.get("tokens_saved", 0),
            compression_ratio=data.get("compression_ratio", 1.0),
        )
