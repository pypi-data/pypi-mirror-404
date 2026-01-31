from enum import Enum
from typing import List, Dict, Any
from pydantic import BaseModel, model_validator


class TrustLevel(str, Enum):
    TRUSTED = "trusted"
    SEMI_TRUSTED = "semi_trusted"
    UNTRUSTED = "untrusted"


class ImpactClass(str, Enum):
    READ = "read"
    WRITE = "write"
    EXTERNAL = "external"
    IRREVERSIBLE = "irreversible"
    MONEY = "money"
    COMPUTE = "compute"
    PRIVACY = "privacy"


class Provenance(BaseModel):
    id: str
    trust: TrustLevel


class Claim(BaseModel):
    text: str
    evidence: List[str]


class ActionProposal(BaseModel):
    protocol: str = "PIC/1.0"
    intent: str
    impact: ImpactClass
    provenance: List[Provenance]
    claims: List[Claim]
    action: Dict[str, Any]

    @model_validator(mode="after")
    def verify_causal_contract(self) -> "ActionProposal":
        # Minimal reference rule: high-impact actions require trusted evidence
        if self.impact in {ImpactClass.MONEY, ImpactClass.IRREVERSIBLE}:
            trusted_ids = {p.id for p in self.provenance if p.trust == TrustLevel.TRUSTED}
            has_trusted_evidence = any(
                any(ev_id in trusted_ids for ev_id in claim.evidence)
                for claim in self.claims
            )
            if not has_trusted_evidence:
                raise ValueError(
                    f"Contract Violation: Action of type '{self.impact}' cannot proceed "
                    f"without evidence from a TRUSTED source."
                )
        return self
