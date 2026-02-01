# Copyright (c) 2024-2026 YuyAI / InsAIts Team. All rights reserved.
# Proprietary and confidential. See LICENSE.premium for terms.
"""
InsAIts Premium - Adaptive Dictionary System
=============================================
Domain-specific dictionaries, adaptive jargon learning,
persistence, and auto-expansion via LLM.
"""

import json
import os
import re
import time
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)

# Try to import LLM for auto-expansion
try:
    from ..local_llm import ollama_chat
    LLM_AVAILABLE = True
except Exception:
    LLM_AVAILABLE = False

# Default cache directory for persisted dictionaries
INSAITS_CACHE_DIR = Path.home() / ".insaits"
JARGON_FILE = INSAITS_CACHE_DIR / "jargon.json"


# ============================================
# Domain-specific dictionaries
# ============================================

DOMAIN_DICTIONARIES: Dict[str, Dict[str, Any]] = {
    "finance": {
        "known": {
            "EBITDA", "P&L", "ROI", "CAGR", "AUM", "NAV", "YTD", "QTD", "MTD",
            "WACC", "DCF", "NPV", "IRR", "EPS", "PE", "PB", "ROIC", "ROCE",
            "CAPEX", "OPEX", "FCF", "LBO", "M&A", "IPO", "SPV", "ABS", "MBS",
            "CDO", "CDS", "OTC", "FX", "FRA", "IRS", "LIBOR", "SOFR", "EURIBOR"
        },
        "expansions": {
            "EBITDA": "Earnings Before Interest, Taxes, Depreciation, and Amortization",
            "WACC": "Weighted Average Cost of Capital",
            "DCF": "Discounted Cash Flow",
            "NPV": "Net Present Value",
            "IRR": "Internal Rate of Return",
            "EPS": "Earnings Per Share",
            "CAPEX": "Capital Expenditure",
            "OPEX": "Operating Expenditure",
            "FCF": "Free Cash Flow",
            "LBO": "Leveraged Buyout",
            "ABS": "Asset-Backed Securities",
            "MBS": "Mortgage-Backed Securities",
            "CDO": "Collateralized Debt Obligation",
            "CDS": "Credit Default Swap"
        }
    },
    "healthcare": {
        "known": {
            "HIPAA", "PHI", "EHR", "EMR", "ICD", "CPT", "DRG", "HMO", "PPO",
            "PCP", "RN", "MD", "DO", "NP", "PA", "ICU", "ER", "OR", "NICU",
            "FDA", "CDC", "WHO", "NIH", "CMS", "HRSA", "ONC", "AHRQ",
            "SNOMED", "LOINC", "HL7", "FHIR", "ADT", "CCR", "CCD", "CCDA"
        },
        "expansions": {
            "HIPAA": "Health Insurance Portability and Accountability Act",
            "PHI": "Protected Health Information",
            "EHR": "Electronic Health Record",
            "EMR": "Electronic Medical Record",
            "ICD": "International Classification of Diseases",
            "CPT": "Current Procedural Terminology",
            "DRG": "Diagnosis-Related Group",
            "FHIR": "Fast Healthcare Interoperability Resources",
            "HL7": "Health Level Seven International",
            "SNOMED": "Systematized Nomenclature of Medicine"
        }
    },
    "kubernetes": {
        "known": {
            "K8S", "POD", "HELM", "KUBECTL", "CRD", "HPA", "VPA", "PVC", "PV",
            "RBAC", "CNI", "CSI", "CRI", "ETCD", "ISTIO", "ENVOY", "NGINX",
            "DAEMONSET", "STATEFULSET", "REPLICASET", "CONFIGMAP", "SECRET",
            "INGRESS", "EGRESS", "SVC", "NS", "SA", "CM", "NODEPORT", "LB"
        },
        "expansions": {
            "K8S": "Kubernetes",
            "HPA": "Horizontal Pod Autoscaler",
            "VPA": "Vertical Pod Autoscaler",
            "PVC": "Persistent Volume Claim",
            "PV": "Persistent Volume",
            "RBAC": "Role-Based Access Control",
            "CNI": "Container Network Interface",
            "CSI": "Container Storage Interface",
            "CRI": "Container Runtime Interface",
            "CRD": "Custom Resource Definition"
        }
    },
    "machine_learning": {
        "known": {
            "BERT", "GPT", "LSTM", "RNN", "CNN", "GAN", "VAE", "AE", "MLP",
            "SOTA", "FLOPS", "TPU", "CUDA", "ONNX", "RLHF", "DPO", "PPO",
            "ADAM", "SGD", "MSE", "MAE", "BCE", "NLL", "KL", "BLEU", "ROUGE",
            "F1", "AUC", "ROC", "PR", "AP", "MAP", "IOU", "YOLO", "RCNN"
        },
        "expansions": {
            "BERT": "Bidirectional Encoder Representations from Transformers",
            "GPT": "Generative Pre-trained Transformer",
            "LSTM": "Long Short-Term Memory",
            "RLHF": "Reinforcement Learning from Human Feedback",
            "DPO": "Direct Preference Optimization",
            "SOTA": "State of the Art",
            "ONNX": "Open Neural Network Exchange",
            "BLEU": "Bilingual Evaluation Understudy",
            "ROUGE": "Recall-Oriented Understudy for Gisting Evaluation"
        }
    },
    "devops": {
        "known": {
            "CI", "CD", "CICD", "IaC", "SRE", "SLO", "SLI", "SLA", "MTTR",
            "MTTF", "MTBF", "RTO", "RPO", "DR", "HA", "FT", "LB", "CDN",
            "APM", "ELK", "SIEM", "WAF", "DDoS", "TLS", "mTLS", "PKI",
            "OIDC", "SAML", "OAuth", "JWT", "JWK", "JWKS"
        },
        "expansions": {
            "CI": "Continuous Integration",
            "CD": "Continuous Deployment/Delivery",
            "IaC": "Infrastructure as Code",
            "SRE": "Site Reliability Engineering",
            "SLO": "Service Level Objective",
            "SLI": "Service Level Indicator",
            "MTTR": "Mean Time To Recovery",
            "MTTF": "Mean Time To Failure",
            "RTO": "Recovery Time Objective",
            "RPO": "Recovery Point Objective"
        }
    },
    "quantum": {
        "known": {
            "QUBIT", "QPU", "QC", "QML", "NISQ", "VQE", "QAOA", "QFT", "QPE",
            "CNOT", "SWAP", "TOFFOLI", "HADAMARD", "PAULI", "BLOCH",
            "IBM", "IBMQ", "CIRQ", "QISKIT", "PENNYLANE", "BRAKET"
        },
        "expansions": {
            "QUBIT": "Quantum Bit",
            "QPU": "Quantum Processing Unit",
            "QML": "Quantum Machine Learning",
            "NISQ": "Noisy Intermediate-Scale Quantum",
            "VQE": "Variational Quantum Eigensolver",
            "QAOA": "Quantum Approximate Optimization Algorithm",
            "QFT": "Quantum Fourier Transform",
            "QPE": "Quantum Phase Estimation"
        }
    }
}


class AdaptiveDictionary:
    """
    Adaptive jargon dictionary with domain-specific knowledge,
    persistence, auto-learning, and LLM-based expansion.

    This is a premium feature that provides:
    - Auto-promotion of frequently seen terms
    - Domain dictionary loading (finance, healthcare, k8s, ML, devops, quantum)
    - Dictionary import/export to JSON
    - LLM-based term expansion via Ollama
    - Persistent storage in ~/.insaits/jargon.json
    """

    CANDIDATE_PROMOTION_THRESHOLD = 5
    MAX_CANDIDATES = 500

    def __init__(self, auto_learn: bool = True, seed_terms: Optional[Set[str]] = None):
        """
        Initialize the adaptive dictionary.

        Args:
            auto_learn: If True, automatically learn new terms from conversations
            seed_terms: Optional set of seed terms to start with
        """
        self.auto_learn = auto_learn

        self.jargon_dict: Dict[str, Any] = {
            "known": seed_terms.copy() if seed_terms else set(),
            "candidate": defaultdict(int),
            "learned": set(),
            "expanded": {}
        }

        self._load_dict()

    def _load_dict(self) -> None:
        """Load persisted jargon dictionary from disk."""
        try:
            if JARGON_FILE.exists():
                with open(JARGON_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                if "learned" in data:
                    self.jargon_dict["learned"] = set(data["learned"])
                if "candidate" in data:
                    self.jargon_dict["candidate"] = defaultdict(int, data["candidate"])
                if "expanded" in data:
                    self.jargon_dict["expanded"] = data["expanded"]

                logger.info(
                    f"Loaded jargon dictionary: "
                    f"{len(self.jargon_dict['learned'])} learned terms"
                )
        except Exception as e:
            logger.warning(f"Could not load jargon dictionary: {e}")

    def _save_dict(self) -> None:
        """Persist jargon dictionary to disk."""
        try:
            INSAITS_CACHE_DIR.mkdir(parents=True, exist_ok=True)

            data = {
                "learned": list(self.jargon_dict["learned"]),
                "candidate": dict(self.jargon_dict["candidate"]),
                "expanded": self.jargon_dict["expanded"],
                "last_updated": time.time()
            }

            with open(JARGON_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)

            logger.debug(
                f"Saved jargon dictionary: "
                f"{len(self.jargon_dict['learned'])} learned terms"
            )
        except Exception as e:
            logger.error(f"Could not save jargon dictionary: {e}", exc_info=True)

    def is_known_term(self, term: str) -> bool:
        """Check if a term is known (seed or learned)."""
        upper = term.upper()
        return (
            upper in self.jargon_dict["known"] or
            upper in self.jargon_dict["learned"]
        )

    def track_candidate(self, term: str) -> bool:
        """
        Track a candidate term and promote if threshold reached.
        Returns True if the term was promoted to learned.
        """
        if not self.auto_learn:
            return False

        upper = term.upper()

        if self.is_known_term(upper):
            return False

        self.jargon_dict["candidate"][upper] += 1

        if self.jargon_dict["candidate"][upper] >= self.CANDIDATE_PROMOTION_THRESHOLD:
            self.jargon_dict["learned"].add(upper)
            del self.jargon_dict["candidate"][upper]
            logger.info(f"Auto-learned new term: {upper}")
            self._save_dict()
            return True

        if len(self.jargon_dict["candidate"]) > self.MAX_CANDIDATES:
            sorted_candidates = sorted(
                self.jargon_dict["candidate"].items(),
                key=lambda x: x[1]
            )
            for term_to_remove, _ in sorted_candidates[:100]:
                del self.jargon_dict["candidate"][term_to_remove]

        return False

    def add_learned_term(self, term: str, expanded: Optional[str] = None) -> None:
        """Manually add a term to the learned dictionary."""
        upper = term.upper()
        self.jargon_dict["learned"].add(upper)
        if expanded:
            self.jargon_dict["expanded"][upper] = expanded
        self._save_dict()
        logger.info(f"Manually added term: {upper}")

    def get_jargon_stats(self) -> Dict:
        """Return statistics about the jargon dictionary."""
        return {
            "known_terms": len(self.jargon_dict["known"]),
            "learned_terms": len(self.jargon_dict["learned"]),
            "candidate_terms": len(self.jargon_dict["candidate"]),
            "expanded_terms": len(self.jargon_dict["expanded"]),
            "top_candidates": dict(
                sorted(
                    self.jargon_dict["candidate"].items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:10]
            )
        }

    # ============================================
    # Domain Dictionary Management
    # ============================================

    def load_domain(self, domain: str) -> Dict:
        """Load a domain-specific dictionary to reduce false positives."""
        if domain not in DOMAIN_DICTIONARIES:
            available = list(DOMAIN_DICTIONARIES.keys())
            return {"error": f"Unknown domain: {domain}", "available_domains": available}

        domain_data = DOMAIN_DICTIONARIES[domain]

        terms_before = len(self.jargon_dict["known"])
        self.jargon_dict["known"].update(domain_data["known"])
        terms_added = len(self.jargon_dict["known"]) - terms_before

        expansions_before = len(self.jargon_dict["expanded"])
        self.jargon_dict["expanded"].update(domain_data.get("expansions", {}))
        expansions_added = len(self.jargon_dict["expanded"]) - expansions_before

        self._save_dict()

        logger.info(f"Loaded domain '{domain}': {terms_added} terms, {expansions_added} expansions")

        return {
            "loaded": domain,
            "terms_added": terms_added,
            "expansions_added": expansions_added,
            "total_known": len(self.jargon_dict["known"]),
            "total_expanded": len(self.jargon_dict["expanded"])
        }

    def get_available_domains(self) -> List[str]:
        """Return list of available domain dictionaries."""
        return list(DOMAIN_DICTIONARIES.keys())

    def export_dictionary(self, filepath: str) -> Dict:
        """Export the current dictionary to a JSON file."""
        data = {
            "known": list(self.jargon_dict["known"]),
            "learned": list(self.jargon_dict["learned"]),
            "expanded": self.jargon_dict["expanded"],
            "metadata": {
                "exported_at": time.time(),
                "version": "2.0",
                "known_count": len(self.jargon_dict["known"]),
                "learned_count": len(self.jargon_dict["learned"]),
                "expanded_count": len(self.jargon_dict["expanded"])
            }
        }

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Exported dictionary to {filepath}")
            return {
                "exported": filepath,
                "total_terms": len(data["known"]) + len(data["learned"]),
                "known_terms": len(data["known"]),
                "learned_terms": len(data["learned"]),
                "expanded_terms": len(data["expanded"])
            }
        except Exception as e:
            logger.error(f"Failed to export dictionary: {e}", exc_info=True)
            return {"error": str(e)}

    def import_dictionary(self, filepath: str, merge: bool = True) -> Dict:
        """Import a dictionary from a JSON file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            known_before = len(self.jargon_dict["known"])
            learned_before = len(self.jargon_dict["learned"])
            expanded_before = len(self.jargon_dict["expanded"])

            if merge:
                self.jargon_dict["known"].update(set(data.get("known", [])))
                self.jargon_dict["learned"].update(set(data.get("learned", [])))
                self.jargon_dict["expanded"].update(data.get("expanded", {}))
            else:
                imported_known = set(data.get("known", []))
                self.jargon_dict["known"] = self.jargon_dict["known"].union(imported_known)
                self.jargon_dict["learned"] = set(data.get("learned", []))
                self.jargon_dict["expanded"] = data.get("expanded", {})

            self._save_dict()

            return {
                "imported": filepath,
                "mode": "merge" if merge else "replace",
                "known_added": len(self.jargon_dict["known"]) - known_before,
                "learned_added": len(self.jargon_dict["learned"]) - learned_before,
                "expanded_added": len(self.jargon_dict["expanded"]) - expanded_before,
                "total_known": len(self.jargon_dict["known"]),
                "total_learned": len(self.jargon_dict["learned"]),
                "total_expanded": len(self.jargon_dict["expanded"])
            }
        except FileNotFoundError:
            return {"error": f"File not found: {filepath}"}
        except json.JSONDecodeError as e:
            return {"error": f"Invalid JSON: {e}"}
        except Exception as e:
            logger.error(f"Failed to import dictionary: {e}", exc_info=True)
            return {"error": str(e)}

    def auto_expand_terms(
        self,
        terms: Optional[List[str]] = None,
        model: str = "phi3"
    ) -> Dict:
        """Use LLM to automatically expand undefined terms."""
        if not LLM_AVAILABLE:
            return {"error": "LLM not available (Ollama required)"}

        if terms is None:
            terms = [
                t for t in self.jargon_dict["learned"]
                if t not in self.jargon_dict["expanded"]
            ]

        if not terms:
            return {"status": "all_terms_expanded", "expanded": {}}

        expansions = {}
        errors = []

        for term in terms[:20]:
            messages = [{
                "role": "user",
                "content": (
                    f"What does the acronym '{term}' stand for? "
                    f"Reply with ONLY the expansion, nothing else. "
                    f"If unknown, reply 'UNKNOWN'."
                )
            }]

            try:
                response = ollama_chat(messages, model=model, temperature=0.1)
                if response and len(response) < 200 and "UNKNOWN" not in response.upper():
                    expansion = response.strip()
                    expansions[term] = expansion
                    self.jargon_dict["expanded"][term] = expansion
            except Exception as e:
                errors.append({"term": term, "error": str(e)})

        if expansions:
            self._save_dict()

        logger.info(f"Auto-expanded {len(expansions)} terms")

        return {
            "expanded": expansions,
            "count": len(expansions),
            "remaining": len(terms) - len(expansions) - len(errors),
            "errors": errors if errors else None
        }

    # ============================================
    # Session Learning
    # ============================================

    def learn_from_session(
        self,
        history: Dict,
        min_occurrences: int = 3,
        auto_save: bool = True
    ) -> Dict:
        """
        Analyze session messages and learn new jargon terms.

        Args:
            history: The conversation history dict from monitor
            min_occurrences: Minimum times a term must appear to be learned
            auto_save: Whether to persist after learning

        Returns:
            Dict with learning statistics
        """
        all_text = []
        for agent_hist in history.values():
            for llm_msgs in agent_hist.values():
                for msg in llm_msgs:
                    all_text.append(msg["text"])

        if not all_text:
            return {
                "status": "no_data",
                "message": "No messages in session to learn from",
                "terms_learned": 0
            }

        full_text = " ".join(all_text)
        acronyms = re.findall(r'\b[A-Z]{2,}\b', full_text)
        term_counts = Counter(acronyms)

        new_terms = []
        skipped_known = []
        skipped_low_count = []

        for term, count in term_counts.items():
            if self.is_known_term(term):
                skipped_known.append(term)
            elif count < min_occurrences:
                skipped_low_count.append((term, count))
            else:
                self.add_learned_term(term)
                new_terms.append((term, count))

        if auto_save and new_terms:
            self._save_dict()

        return {
            "status": "success",
            "terms_learned": len(new_terms),
            "learned_terms": new_terms,
            "already_known": len(skipped_known),
            "below_threshold": len(skipped_low_count),
            "jargon_stats": self.get_jargon_stats()
        }
