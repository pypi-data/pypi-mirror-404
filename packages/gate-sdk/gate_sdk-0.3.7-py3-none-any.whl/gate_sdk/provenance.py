"""
Provenance Provider

Provides provenance information (repo, workflow, attestation) from environment variables.
Used for CI/CD provenance enforcement in Gate.
"""

import os
from typing import Optional, Dict, Any


class Provenance:
    """Provenance information extracted from environment"""

    def __init__(
        self,
        repo: Optional[str] = None,
        workflow: Optional[str] = None,
        ref: Optional[str] = None,
        actor: Optional[str] = None,
        attestation: Optional[Dict[str, Any]] = None,
    ):
        self.repo = repo
        self.workflow = workflow
        self.ref = ref
        self.actor = actor
        self.attestation = attestation

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for request body"""
        result: Dict[str, Any] = {}
        if self.repo:
            result["repo"] = self.repo
        if self.workflow:
            result["workflow"] = self.workflow
        if self.ref:
            result["ref"] = self.ref
        if self.actor:
            result["actor"] = self.actor
        if self.attestation:
            result["attestation"] = self.attestation
        return result


class ProvenanceProvider:
    """
    Provenance Provider

    Reads provenance information from environment variables:
    - GATE_CALLER_REPO
    - GATE_CALLER_WORKFLOW
    - GATE_CALLER_REF
    - GATE_CALLER_ACTOR
    - GATE_ATTESTATION_VALID
    - GATE_ATTESTATION_ISSUER
    - GATE_ATTESTATION_SUBJECT
    - GATE_ATTESTATION_SHA
    """

    @staticmethod
    def get_provenance() -> Optional[Provenance]:
        """
        Get provenance from environment variables

        Returns:
            Provenance object or None if no env vars are set
        """
        repo = os.getenv("GATE_CALLER_REPO")
        workflow = os.getenv("GATE_CALLER_WORKFLOW")
        ref = os.getenv("GATE_CALLER_REF")
        actor = os.getenv("GATE_CALLER_ACTOR")
        attestation_valid = os.getenv("GATE_ATTESTATION_VALID")
        attestation_issuer = os.getenv("GATE_ATTESTATION_ISSUER")
        attestation_subject = os.getenv("GATE_ATTESTATION_SUBJECT")
        attestation_sha = os.getenv("GATE_ATTESTATION_SHA")

        # If no provenance env vars are set, return None
        if not any([repo, workflow, ref, actor, attestation_valid]):
            return None

        # Build attestation if any attestation env vars are set
        attestation = None
        if any([attestation_valid, attestation_issuer, attestation_subject, attestation_sha]):
            attestation = {
                "valid": attestation_valid in ("true", "1", "True"),
                "issuer": attestation_issuer,
                "subject": attestation_subject,
                "sha": attestation_sha,
            }

        return Provenance(
            repo=repo,
            workflow=workflow,
            ref=ref,
            actor=actor,
            attestation=attestation,
        )

    @staticmethod
    def is_enabled() -> bool:
        """
        Check if provenance is enabled (env vars present)

        Returns:
            True if provenance env vars are set
        """
        return bool(
            os.getenv("GATE_CALLER_REPO")
            or os.getenv("GATE_CALLER_WORKFLOW")
            or os.getenv("GATE_ATTESTATION_VALID")
        )

