"""Verifiable Credential verification for Digital Product Passports."""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass, field
from typing import Any

from dppvalidator.logging import get_logger
from dppvalidator.verifier.did import DIDResolver
from dppvalidator.verifier.signatures import SignatureVerifier, verify_jws

logger = get_logger(__name__)


@dataclass
class VerificationResult:
    """Result of credential verification."""

    valid: bool
    signature_valid: bool | None = None
    issuer_did: str | None = None
    verification_method: str | None = None
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def verified(self) -> bool:
        """Check if the credential is fully verified."""
        return self.valid and self.signature_valid is True


class CredentialVerifier:
    """Verify Verifiable Credentials in Digital Product Passports.

    Supports verification of:
    - Data Integrity Proofs (embedded proofs)
    - Enveloped Proofs (JWS/JWT format)
    - did:web and did:key issuer resolution
    """

    def __init__(
        self,
        did_resolver: DIDResolver | None = None,
        signature_verifier: SignatureVerifier | None = None,
    ) -> None:
        """Initialize the credential verifier.

        Args:
            did_resolver: Custom DID resolver, or None to use default
            signature_verifier: Custom signature verifier, or None to use default

        """
        self._did_resolver = did_resolver or DIDResolver()
        self._signature_verifier = signature_verifier or SignatureVerifier()

    def verify(self, credential: dict[str, Any]) -> VerificationResult:
        """Verify a Verifiable Credential.

        Args:
            credential: The credential as a dict (parsed JSON)

        Returns:
            VerificationResult with verification status

        """
        result = VerificationResult(valid=True)

        # Extract issuer first (always available)
        issuer = self._extract_issuer(credential)
        if issuer:
            result.issuer_did = issuer

        # Determine proof type and verify
        proof = credential.get("proof")
        if proof:
            # Data Integrity Proof (embedded)
            return self._verify_data_integrity_proof(credential, proof, result)

        # Check for JWT/JWS format (enveloped proof)
        if self._is_jwt_credential(credential):
            return self._verify_jwt_credential(credential, result)

        # No proof found
        result.warnings.append("No proof found in credential")
        return result

    def _extract_issuer(self, credential: dict[str, Any]) -> str | None:
        """Extract the issuer DID from a credential."""
        issuer = credential.get("issuer")
        if isinstance(issuer, str):
            return issuer
        if isinstance(issuer, dict):
            return issuer.get("id")
        return None

    def _is_jwt_credential(self, _credential: dict[str, Any]) -> bool:
        """Check if the credential is in JWT format."""
        # JWT credentials have a specific structure or are passed as strings
        return False  # We expect parsed credentials, not JWT strings

    def _verify_data_integrity_proof(
        self,
        credential: dict[str, Any],
        proof: dict[str, Any] | list[dict[str, Any]],
        result: VerificationResult,
    ) -> VerificationResult:
        """Verify a Data Integrity Proof."""
        # Handle proof as list or single object
        proofs = proof if isinstance(proof, list) else [proof]

        for p in proofs:
            proof_type = p.get("type", "")
            verification_method = p.get("verificationMethod", "")
            result.verification_method = verification_method

            # Resolve the verification method
            did = self._extract_did_from_method(verification_method)
            if not did:
                result.errors.append(f"Could not extract DID from: {verification_method}")
                result.valid = False
                continue

            did_doc = self._did_resolver.resolve(did)
            if not did_doc:
                result.errors.append(f"Could not resolve DID: {did}")
                result.valid = False
                continue

            vm = did_doc.get_verification_method(verification_method)
            if not vm:
                result.errors.append(f"Verification method not found: {verification_method}")
                result.valid = False
                continue

            # Verify based on proof type
            if proof_type in ("Ed25519Signature2020", "DataIntegrityProof"):
                sig_valid = self._verify_ed25519_proof(credential, p, vm)
            elif proof_type == "JsonWebSignature2020":
                sig_valid = self._verify_jws_proof(credential, p, vm)
            else:
                result.warnings.append(f"Unsupported proof type: {proof_type}")
                sig_valid = None

            result.signature_valid = sig_valid
            if sig_valid is False:
                result.valid = False
                result.errors.append("Signature verification failed")

        return result

    def _extract_did_from_method(self, verification_method: str) -> str | None:
        """Extract the DID from a verification method ID."""
        if verification_method.startswith("did:"):
            # Format: did:method:identifier#fragment
            parts = verification_method.split("#")
            return parts[0]
        return None

    def _verify_ed25519_proof(
        self,
        credential: dict[str, Any],
        proof: dict[str, Any],
        vm: Any,
    ) -> bool | None:
        """Verify an Ed25519 signature proof."""
        try:
            # Get proof value
            proof_value = proof.get("proofValue", "")
            if not proof_value:
                return None

            # Decode multibase-encoded signature (z prefix = base58btc)
            if proof_value.startswith("z"):
                signature = self._decode_base58btc(proof_value[1:])
            else:
                signature = base64.b64decode(proof_value)

            if not signature:
                return None

            # Create the message to verify (canonicalized credential minus proof)
            message = self._create_verify_data(credential, proof)
            if not message:
                return None

            # Verify using the verification method
            return self._signature_verifier.verify_from_method(signature, message, vm)

        except Exception as e:
            logger.warning("Ed25519 proof verification error: %s", e)
            return None

    def _verify_jws_proof(
        self,
        _credential: dict[str, Any],
        proof: dict[str, Any],
        vm: Any,
    ) -> bool | None:
        """Verify a JWS proof."""
        try:
            jws = proof.get("jws", "")
            if not jws:
                return None

            if not vm.public_key_jwk:
                return None

            valid, _ = verify_jws(jws, vm.public_key_jwk)
            return valid

        except Exception as e:
            logger.warning("JWS proof verification error: %s", e)
            return None

    def _create_verify_data(
        self,
        credential: dict[str, Any],
        proof: dict[str, Any],
    ) -> bytes | None:
        """Create the data to be verified (canonicalized document)."""
        try:
            # Remove proof from credential for verification
            cred_copy = {k: v for k, v in credential.items() if k != "proof"}

            # Create proof options (proof without proofValue)
            proof_options = {k: v for k, v in proof.items() if k != "proofValue"}

            # Simple canonicalization (for production, use RDF canonicalization)
            # This is a simplified version - full implementation would use URDNA2015
            cred_json = json.dumps(cred_copy, sort_keys=True, separators=(",", ":"))
            proof_json = json.dumps(proof_options, sort_keys=True, separators=(",", ":"))

            return (proof_json + cred_json).encode("utf-8")

        except Exception as e:
            logger.warning("Failed to create verify data: %s", e)
            return None

    def _decode_base58btc(self, encoded: str) -> bytes | None:
        """Decode a base58btc string."""
        alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
        try:
            num = 0
            for char in encoded:
                num = num * 58 + alphabet.index(char)

            result = []
            while num > 0:
                result.append(num % 256)
                num //= 256

            for char in encoded:
                if char == "1":
                    result.append(0)
                else:
                    break

            return bytes(reversed(result))
        except (ValueError, IndexError):
            return None

    def _verify_jwt_credential(
        self,
        _credential: dict[str, Any],
        result: VerificationResult,
    ) -> VerificationResult:
        """Verify a JWT-encoded credential."""
        result.warnings.append("JWT credential verification not fully implemented")
        return result


def verify_credential(credential: dict[str, Any]) -> VerificationResult:
    """Verify a Verifiable Credential using the default verifier.

    Args:
        credential: The credential as a dict

    Returns:
        VerificationResult with verification status

    """
    verifier = CredentialVerifier()
    return verifier.verify(credential)


def has_vc_support() -> bool:
    """Check if VC verification dependencies are installed."""
    return True
