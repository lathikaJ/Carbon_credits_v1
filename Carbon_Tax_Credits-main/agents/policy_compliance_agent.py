"""
Policy & Compliance Agent RAG (Agent 3)
========================================
An autonomous, deterministic industrial AI component responsible for cross-referencing
factory carbon metrics and emission outputs against external legal regulations and
environmental policies using Retrieval-Augmented Generation (RAG) with a Hybrid Search Engine.

Mathematical & Vector Formulations Executed:
1. Semantic Similarity Vector Search (Cosine Similarity):
   Score_vector(q, p) = (v_q . v_p) / (||v_q|| * ||v_p||)

2. BM25 Lexical Keyword Scoring:
   Score_bm25(q, D) = sum_{t in q} IDF(t) * (f(t, D) * (k1 + 1)) / (f(t, D) + k1 * (1 - b + b * (|D| / avgdl)))
   Normalized: Score_bm25_norm(q, D) = Score_bm25(q, D) / max(Score_bm25) (if max > 0 else 0.0)

3. Exact Standard Code & Article Keyword Boosting:
   Score_boost(q, p) = sum_{code in Standard_Codes} W_code * I(code in q and code in p)
                     + sum_{art in Article_Patterns} W_art * I(art in q and art in p)
                     + sum_{v in Version_Tags} W_ver * I(v in q and v in p)

4. Hybrid Retrieval Fusion Ranking:
   Score_hybrid(q, p) = alpha * Score_vector(q, p) + (1 - alpha) * Score_bm25_norm(q, p) + Score_boost(q, p)

5. Deterministic Compliance Boolean Gate:
   Compliance_Status = PASS if (Emission_Intensity_kgco2_per_kwh <= Threshold_regulatory) AND (Verification_Status == 'VERIFIED')
   else FLAGGED_REQUIRES_EXTERNAL_AUDIT.

6. Confidence Score Assignment:
   Confidence_Score = min(0.95, Score(q, p*)) * Data_Reliability_Factor

Execution Rules & Guardrails:
- Rule 1: If data status is 'ESTIMATED_PROXY' or 'REQUIRES_PLANT_SPECIFIC_VERIFICATION', automatically set compliance status to 'PENDING_AUDIT'.
- Rule 2: Guard against hallucinated laws; cite exact document source, clause, and effective reporting year.
- Rule 3: Output strict JSON schema with 'line_code', 'retrieved_policy_id', 'cosine_similarity_score', 'hybrid_score', 'compliance_status', 'verification_mandate', and 'confidence_score'.
- Rule 4: Maintain absolute traceability back to upstream Carbon_Emission metrics and downstream Tax_Incentive_Screening targets.
- Rule 5: If retrieval similarity drops below 0.70, flag context as 'OUT_OF_DOMAIN_POLICY' and trigger manual legal review notification.
"""

import math
import os
import json
import logging
import re
from typing import Dict, List, Any, Optional, Tuple, Union

try:
    from rank_bm25 import BM25Okapi
except ImportError:
    # Pure-Python fallback BM25Okapi when package is not yet installed in local environment
    class BM25Okapi:  # type: ignore
        def __init__(self, corpus: List[List[str]], k1: float = 1.5, b: float = 0.75, epsilon: float = 0.25):
            self.corpus_size = len(corpus)
            self.avgdl = sum(len(x) for x in corpus) / self.corpus_size if self.corpus_size > 0 else 0.0
            self.corpus = corpus
            self.k1 = float(k1)
            self.b = float(b)
            self.epsilon = float(epsilon)
            self.doc_len = [len(x) for x in corpus]
            self.doc_freqs: List[Dict[str, int]] = []
            self.nd: Dict[str, int] = {}
            self.idf: Dict[str, float] = {}
            self._calc_idf()

        def _calc_idf(self):
            for doc in self.corpus:
                frequencies: Dict[str, int] = {}
                for word in doc:
                    frequencies[word] = frequencies.get(word, 0) + 1
                self.doc_freqs.append(frequencies)
                for word in frequencies:
                    self.nd[word] = self.nd.get(word, 0) + 1

            idf_sum = 0.0
            negative_idfs = []
            for word, freq in self.nd.items():
                idf = math.log((self.corpus_size - freq + 0.5) / (freq + 0.5) + 1.0)
                self.idf[word] = idf
                idf_sum += idf
                if idf < 0:
                    negative_idfs.append(word)

            average_idf = float(idf_sum) / len(self.idf) if self.idf else 0.0
            eps = self.epsilon * average_idf
            for word in negative_idfs:
                self.idf[word] = eps

        def get_scores(self, query: List[str]) -> List[float]:
            scores = [0.0] * self.corpus_size
            if not self.corpus_size:
                return scores
            avg_len = self.avgdl if self.avgdl > 0 else 1.0
            for q in query:
                idf = self.idf.get(q, 0.0)
                if idf <= 0.0:
                    continue
                for i in range(self.corpus_size):
                    freq = self.doc_freqs[i].get(q, 0)
                    if freq > 0:
                        numerator = freq * (self.k1 + 1.0)
                        denominator = freq + self.k1 * (1.0 - self.b + self.b * (self.doc_len[i] / avg_len))
                        if denominator > 0:
                            scores[i] += idf * (numerator / denominator)
            return scores

try:
    import pandas as pd
except ImportError:
    pd = None  # type: ignore

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("PolicyComplianceAgent")


# Structured Policy Knowledge Base for RAG vector & BM25 hybrid retrieval
POLICY_KNOWLEDGE_BASE: List[Dict[str, Any]] = [
    {
        "policy_id": "POL-001",
        "policy_name": "CEA National Grid Intensity Standard 2026",
        "jurisdiction": "India (CEA)",
        "effective_year": "2026",
        "clause": "Section 4.1 Grid OM Baseline Thresholds",
        "regulatory_threshold_kgco2_per_kwh": 0.750,
        "vector": [0.716, 0.85, 0.90, 0.80],
        "domain": "Power & Energy Emission Intensity",
        "mandate": "MANDATORY_ANNUAL_REPORTING",
        "standard_code": "CEA Grid Baseline v4 / CEA-EF-2026-V1.4",
        "content": (
            "CENTRAL ELECTRICITY AUTHORITY (CEA) GRID EMISSION FACTOR BASELINE 2026. "
            "Document Ref: CEA-EF-2026-V1.4 | Jurisdiction: India (National Grid). "
            "CEA Grid Baseline v4 Standard. Section 4.1 Grid Operating Margin (OM) Emission Factor Baseline Thresholds. "
            "The weighted average grid emission factor for the All-India regional grid is established at 0.716 kg CO2/kWh. "
            "Industrial manufacturing lines utilizing unmetered grid power allocations must benchmark calculations "
            "against the 0.750 kg CO2/kWh regulatory threshold limit. Any line exceeding 0.750 kg CO2/kWh requires external audit."
        ),
    },
    {
        "policy_id": "POL-002",
        "policy_name": "National Industrial Decarbonization Mandate (NIDM-2025)",
        "jurisdiction": "Federal / National",
        "effective_year": "2025",
        "clause": "Clause 12b Production Intensity Limits",
        "regulatory_threshold_kgco2_per_kwh": 0.800,
        "vector": [0.800, 0.75, 0.85, 0.65],
        "domain": "Industrial Manufacturing Emission Caps",
        "mandate": "THIRD_PARTY_VERIFICATION_REQUIRED",
        "standard_code": "NIDM-2025-SEC12B",
        "content": (
            "NATIONAL INDUSTRIAL DECARBONIZATION MANDATE (NIDM-2025). "
            "Document Ref: NIDM-2025-SEC12B | Clause 12b Production Intensity Limits. "
            "Industrial production facilities must limit carbon intensity per production unit below 0.800 kg CO2/kWh. "
            "Mandatory third-party verification required for credit issuance and compliance certification."
        ),
    },
    {
        "policy_id": "POL-003",
        "policy_name": "VERRA GHG Voluntary Accounting Standard v4.4",
        "jurisdiction": "International Voluntary Registry",
        "effective_year": "2024",
        "clause": "Annex III Energy Efficiency & Proxy Baselines",
        "regulatory_threshold_kgco2_per_kwh": 0.700,
        "vector": [0.700, 0.90, 0.95, 0.85],
        "domain": "Carbon Credit Methodologies",
        "mandate": "REGISTRY_INSPECTION_MANDATORY",
        "standard_code": "VERRA-METH-2024-ANNEX3 v4.4",
        "content": (
            "VERRA / CDM CARBON CREDIT REGISTRATION & METHODOLOGY MANDATE v4.4. "
            "Document Ref: VERRA-METH-2024-ANNEX3 | Jurisdiction: International Registry. "
            "Annex III Additionality, Baseline Determination, Energy Efficiency & Proxy Baselines, and MRV Verification Rules. "
            "1. Baseline Emissions: Computed as the arithmetic mean of daily CO2 emissions over the line's first 7 operating days. "
            "2. Additionality & Verification: Automated credit issuance is blocked unless Methodology_Required, Additionality_Required, "
            "and Verification_Required boolean flags are satisfied and verified by an independent accredited MRV auditor."
        ),
    },
    {
        "policy_id": "POL-004",
        "policy_name": "ISO 14064-1 Organizational Carbon Verification",
        "jurisdiction": "Global Standards Organization",
        "effective_year": "2026",
        "clause": "Section 6.2 Data Reliability & Audit Assurance",
        "regulatory_threshold_kgco2_per_kwh": 0.716,
        "vector": [0.716, 0.80, 0.88, 0.75],
        "domain": "GHG Assertion Verification",
        "mandate": "INDEPENDENT_MRV_MANDATE",
        "standard_code": "ISO 14064-1:2026",
        "content": (
            "ISO 14064-1 ORGANIZATIONAL CARBON VERIFICATION STANDARD. "
            "Document Ref: ISO-14064-1-2026 | Jurisdiction: Global Standards Organization. "
            "Section 6.2 Data Reliability & Audit Assurance. "
            "Specifies principles and requirements at the organization level for quantification and reporting of greenhouse gas (GHG) emissions and removals. "
            "Requires independent MRV mandate and evidence of direct metering verification for emission allocations."
        ),
    },
]


class PolicyComplianceAgent:
    """
    Agent 3: Policy & Compliance Agent (Hybrid RAG)
    Cross-references plant carbon metrics against policy regulations using a Hybrid Search Engine:
    Semantic Vector Cosine Similarity + BM25 Lexical Keyword Scoring + Exact Standard Code Boosting.
    """

    COSINE_THRESHOLD_DOMAIN_GUARD: float = 0.70
    DEFAULT_HYBRID_ALPHA: float = 0.50
    DEFAULT_KEYWORD_BOOST_WEIGHT: float = 0.50

    # Regex patterns for exact regulatory standard codes and authorities
    STANDARD_CODE_PATTERNS = [
        # CEA Grid Baseline & reference numbers
        r'\bcea[\s\-_]*(?:grid[\s\-_]*)?(?:baseline)?(?:[\s\-_]*v?\d+(?:\.\d+)*)?\b',
        r'\bcea[\s\-_]*ef[\s\-_]*\S+\b',
        # ISO 14064 standards
        r'\biso[\s\-_]*14064(?:[\s\-_]*\d+)?(?::\d+)?\b',
        # VERRA / CDM registry mandates
        r'\bverra(?:[\s\-_]*meth[\s\-_]*\S+)?\b',
        r'\bcdm\b',
        # NIDM regulations
        r'\bnidm(?:[\s\-_]*\d+)?\b',
        # NGMTIA acts
        r'\bngmtia(?:[\s\-_]*\d+)?(?:[\s\-_]*sec\w+)?\b',
        # Standalone CEA authority code
        r'\bcea\b',
    ]

    # Regex patterns for standard legal/regulatory article, section, and clause numbers
    ARTICLE_NUMBER_PATTERNS = [
        r'\bsection\s+\d+(?:\.\d+)*[a-z]?\b',
        r'\bclause\s+\d+[a-z]?\b',
        r'\bannex\s+(?:[ivxlcdm]+|\d+)\b',
        r'\barticle\s+\d+[a-z]?\b',
        r'\brule\s+\d+[a-z]?\b',
    ]

    # Regex patterns for version tags (e.g. v4, v4.4, v1.4)
    VERSION_PATTERNS = [
        r'\bv\d+(?:\.\d+)*\b',
    ]

    def __init__(
        self,
        knowledge_base: Optional[List[Dict[str, Any]]] = None,
        cosine_threshold_guard: float = COSINE_THRESHOLD_DOMAIN_GUARD,
        knowledge_dir: Optional[str] = "knowledge_base",
        alpha: float = DEFAULT_HYBRID_ALPHA,
        keyword_boost_weight: float = DEFAULT_KEYWORD_BOOST_WEIGHT,
    ):
        self.knowledge_base = list(knowledge_base or POLICY_KNOWLEDGE_BASE)
        self.cosine_threshold_guard = float(cosine_threshold_guard)
        self.alpha = float(alpha)
        self.keyword_boost_weight = float(keyword_boost_weight)
        self.bm25: Optional[BM25Okapi] = None
        self.corpus_tokens: List[List[str]] = []

        # Build initial BM25 index over default knowledge base
        self._build_bm25_index()

        # Dynamically load chunks from knowledge_base directory if available
        if knowledge_dir:
            resolved_dir = knowledge_dir
            if not os.path.exists(resolved_dir):
                alt1 = os.path.join(os.path.dirname(__file__), "..", knowledge_dir)
                alt2 = os.path.join("Carbon_Tax_Credits-main", knowledge_dir)
                if os.path.exists(alt1):
                    resolved_dir = alt1
                elif os.path.exists(alt2):
                    resolved_dir = alt2
            if os.path.exists(resolved_dir):
                self.load_knowledge_base_from_dir(resolved_dir)

    @staticmethod
    def tokenize(text: str) -> List[str]:
        """
        Tokenizes text into normalized lexical tokens for BM25 indexing and querying.
        Preserves standard codes, clause numbers, and version tags.
        """
        if not text:
            return []
        raw_tokens = re.findall(r'[a-zA-Z0-9_\.\-]+', text.lower())
        tokens = []
        for token in raw_tokens:
            cleaned = token.strip(".-_")
            if cleaned:
                tokens.append(cleaned)
                sub_parts = re.split(r'[\.\-_]+', cleaned)
                if len(sub_parts) > 1:
                    tokens.extend([p for p in sub_parts if p and p != cleaned])
        return tokens

    def _get_chunk_searchable_text(self, chunk: Dict[str, Any]) -> str:
        """Constructs an exhaustive searchable string representation of a policy chunk."""
        parts = [
            str(chunk.get("policy_id", "")),
            str(chunk.get("policy_name", "")),
            str(chunk.get("clause", "")),
            str(chunk.get("standard_code", "")),
            str(chunk.get("domain", "")),
            str(chunk.get("jurisdiction", "")),
            str(chunk.get("mandate", "")),
            str(chunk.get("content", "")),
            str(chunk.get("content_snippet", "")),
        ]
        return " ".join(p for p in parts if p)

    def _build_bm25_index(self):
        """Constructs the BM25 index over all documents currently in self.knowledge_base."""
        self.corpus_tokens = []
        for chunk in self.knowledge_base:
            text = self._get_chunk_searchable_text(chunk)
            tokens = self.tokenize(text)
            self.corpus_tokens.append(tokens)

        if self.corpus_tokens:
            self.bm25 = BM25Okapi(self.corpus_tokens)
        else:
            self.bm25 = None

    def compute_keyword_boost(self, query_text: str, chunk: Dict[str, Any]) -> float:
        """
        Calculates keyword boost for exact standard codes (e.g., 'CEA Grid Baseline v4', 'ISO 14064-1')
        and standard article/clause numbers (e.g., 'Section 4.1', 'Clause 12b', 'Annex III').
        """
        if not query_text:
            return 0.0

        q_lower = query_text.lower().strip()
        chunk_text = self._get_chunk_searchable_text(chunk).lower()
        boost = 0.0

        # 1. Exact Standard Codes Boosting
        for pattern in self.STANDARD_CODE_PATTERNS:
            for match in re.finditer(pattern, q_lower):
                matched_str = match.group().strip()
                if len(matched_str) >= 3 and matched_str in chunk_text:
                    boost += self.keyword_boost_weight

        # 2. Standard Article / Clause Numbers Boosting (high-precision references)
        for pattern in self.ARTICLE_NUMBER_PATTERNS:
            for match in re.finditer(pattern, q_lower):
                matched_str = match.group().strip()
                if matched_str in chunk_text:
                    boost += self.keyword_boost_weight * 1.5

        # 3. Exact Version Tags (e.g. v4, v4.4)
        for pattern in self.VERSION_PATTERNS:
            for match in re.finditer(pattern, q_lower):
                matched_str = match.group().strip()
                if matched_str in chunk_text:
                    boost += self.keyword_boost_weight * 0.5
                elif matched_str.startswith("v") and matched_str[1:] in chunk_text:
                    boost += self.keyword_boost_weight * 0.3

        # 4. Multi-word phrase exact matches
        important_phrases = [
            "cea grid baseline",
            "grid baseline",
            "grid emission factor",
            "grid operating margin",
            "grid om baseline",
            "voluntary accounting standard",
            "carbon credit registration",
            "green manufacturing",
            "capital allowances",
            "organizational carbon verification",
            "additionality",
        ]
        for phrase in important_phrases:
            if phrase in q_lower and phrase in chunk_text:
                boost += self.keyword_boost_weight

        # 5. Direct Policy ID match (e.g. POL-001, POL-KB-006)
        policy_id = str(chunk.get("policy_id", "")).lower()
        if policy_id and policy_id in q_lower:
            boost += self.keyword_boost_weight * 2.0

        return boost

    def load_knowledge_base_from_dir(self, knowledge_dir: str = "knowledge_base"):
        """
        Dynamically scans knowledge_base/ directory for .txt documents,
        extracts regulatory chunks, and adds vector embeddings and BM25 tokens to RAG search store.
        """
        import glob
        resolved_dir = knowledge_dir
        if not os.path.exists(resolved_dir):
            alt1 = os.path.join(os.path.dirname(__file__), "..", knowledge_dir)
            alt2 = os.path.join("Carbon_Tax_Credits-main", knowledge_dir)
            if os.path.exists(alt1):
                resolved_dir = alt1
            elif os.path.exists(alt2):
                resolved_dir = alt2
            else:
                return

        txt_files = glob.glob(os.path.join(resolved_dir, "*.txt"))
        for idx, filepath in enumerate(sorted(txt_files), start=5):
            filename = os.path.basename(filepath)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()

                policy_id = f"POL-KB-{idx:03d}"
                lines = [line.strip() for line in content.strip().split("\n") if line.strip()]

                policy_name = lines[0] if lines else filename.replace(".txt", "").replace("_", " ").upper()
                jurisdiction = "Knowledge Base Document"
                clause = f"Ingested Document Chunk ({filename})"
                threshold = 0.750
                vector = [0.716, 0.85, 0.90, 0.80]
                domain = "Dynamic Ingested Policy Chunk"
                mandate = "DYNAMIC_KB_AUDIT"
                standard_code = ""

                for line in lines:
                    if "Document Ref:" in line:
                        ref_parts = line.split("|")
                        standard_code = ref_parts[0].replace("Document Ref:", "").strip()
                        if len(ref_parts) > 1 and "Jurisdiction:" in ref_parts[1]:
                            jurisdiction = ref_parts[1].replace("Jurisdiction:", "").strip()
                    elif line.startswith("Section ") or line.startswith("Clause ") or line.startswith("Annex "):
                        clause = line.strip()

                if "cea" in filename.lower() or "grid" in filename.lower():
                    vector = [0.716, 0.85, 0.90, 0.80]
                    threshold = 0.750
                    domain = "Power & Energy Emission Intensity"
                    mandate = "MANDATORY_ANNUAL_REPORTING"
                    standard_code = standard_code or "CEA Grid Baseline v4 / CEA-EF-2026-V1.4"
                elif "tax" in filename.lower() or "incentive" in filename.lower():
                    vector = [0.450, 0.80, 0.85, 0.75]
                    threshold = 0.450
                    domain = "Green Manufacturing Tax Incentives"
                    mandate = "TAX_SCREENING_AUDIT"
                    standard_code = standard_code or "NGMTIA-2025-SEC12B"
                elif "registry" in filename.lower() or "verra" in filename.lower() or "carbon_credit" in filename.lower():
                    vector = [0.700, 0.90, 0.95, 0.85]
                    threshold = 0.700
                    domain = "Carbon Credit Methodologies"
                    mandate = "REGISTRY_INSPECTION_MANDATORY"
                    standard_code = standard_code or "VERRA-METH-2024-ANNEX3 v4.4"

                chunk = {
                    "policy_id": policy_id,
                    "policy_name": policy_name,
                    "jurisdiction": jurisdiction,
                    "effective_year": "2026",
                    "clause": clause,
                    "regulatory_threshold_kgco2_per_kwh": threshold,
                    "vector": vector,
                    "domain": domain,
                    "mandate": mandate,
                    "standard_code": standard_code,
                    "content": content,
                    "content_snippet": content[:200],
                    "source_file": filename,
                }

                if not any(k.get("policy_id") == policy_id for k in self.knowledge_base):
                    self.knowledge_base.append(chunk)
                    logger.info(f"PolicyComplianceAgent (Hybrid RAG): Dynamically indexed {filename} into vector store & BM25 corpus.")
            except Exception as e:
                logger.warning(f"Failed to ingest knowledge base file {filename}: {e}")

        self._build_bm25_index()

    # ------------------------------------------------------------------
    # Dynamic Chunking, Hybrid Index Rebuild, and Knowledge Base Reload
    # ------------------------------------------------------------------

    def chunk_text_documents(
        self,
        knowledge_dir: str = "knowledge_base/",
        chunk_size: int = 500,
        overlap: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Sliding window chunker: splits .txt files into overlapping text blocks
        with source metadata citations attached (source_file, chunk_id).

        Args:
            knowledge_dir: Path to directory containing .txt policy files.
            chunk_size:    Number of words per chunk window (default 500).
            overlap:       Number of words to overlap between chunks (default 100).

        Returns:
            List of chunk dicts with keys: chunk_id, source_file, text, start_word, end_word.
        """
        import glob
        chunks: List[Dict[str, Any]] = []
        chunk_id = 0

        # Resolve directory path robustly
        resolved_dir = knowledge_dir
        if not os.path.exists(resolved_dir):
            alt1 = os.path.join(os.path.dirname(__file__), "..", knowledge_dir)
            alt2 = os.path.join("Carbon_Tax_Credits-main", knowledge_dir)
            if os.path.exists(alt1):
                resolved_dir = alt1
            elif os.path.exists(alt2):
                resolved_dir = alt2
            else:
                logger.warning(f"chunk_text_documents: directory not found: {knowledge_dir}")
                return chunks

        txt_files = glob.glob(os.path.join(resolved_dir, "*.txt"))
        for filepath in sorted(txt_files):
            filename = os.path.basename(filepath)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    text = f.read()
                words = text.split()
                if not words:
                    continue
                start = 0
                while start < len(words):
                    end = min(start + chunk_size, len(words))
                    chunk_text = " ".join(words[start:end])
                    chunks.append({
                        "chunk_id": chunk_id,
                        "source_file": filename,
                        "text": chunk_text,
                        "start_word": start,
                        "end_word": end,
                    })
                    chunk_id += 1
                    if end >= len(words):
                        break
                    start += chunk_size - overlap
            except Exception as e:
                logger.warning(f"chunk_text_documents: failed to chunk '{filename}': {e}")

        logger.info(f"chunk_text_documents: produced {len(chunks)} chunks from {len(txt_files)} files in '{resolved_dir}'.")
        return chunks

    def build_hybrid_index(self, chunks: List[Dict[str, Any]]) -> None:
        """
        Regenerates the BM25 index and knowledge_base entries from sliding-window text chunks.
        Merges with base POL-001..POL-004 entries; replaces prior POL-CHUNK- entries.

        Args:
            chunks: List of chunk dicts from chunk_text_documents().
        """
        new_entries: List[Dict[str, Any]] = []
        for chunk in chunks:
            src = chunk["source_file"]
            # Inherit domain/mandate/threshold heuristics from filename
            if "cea" in src.lower() or "grid" in src.lower():
                vector = [0.716, 0.85, 0.90, 0.80]
                threshold = 0.750
                domain = "Power & Energy Emission Intensity"
                mandate = "MANDATORY_ANNUAL_REPORTING"
                standard_code = "CEA Grid Baseline v4 / CEA-EF-2026-V1.4"
            elif "tax" in src.lower() or "incentive" in src.lower():
                vector = [0.450, 0.80, 0.85, 0.75]
                threshold = 0.450
                domain = "Green Manufacturing Tax Incentives"
                mandate = "TAX_SCREENING_AUDIT"
                standard_code = "NGMTIA-2025-SEC12B"
            elif "registry" in src.lower() or "verra" in src.lower() or "carbon_credit" in src.lower():
                vector = [0.700, 0.90, 0.95, 0.85]
                threshold = 0.700
                domain = "Carbon Credit Methodologies"
                mandate = "REGISTRY_INSPECTION_MANDATORY"
                standard_code = "VERRA-METH-2024-ANNEX3 v4.4"
            else:
                vector = [0.716, 0.85, 0.90, 0.80]
                threshold = 0.750
                domain = "Dynamic Chunked Policy Text"
                mandate = "DYNAMIC_CHUNK_AUDIT"
                standard_code = ""

            entry = {
                "policy_id": f"POL-CHUNK-{chunk['chunk_id']:04d}",
                "policy_name": src.replace(".txt", "").replace("_", " ").upper(),
                "jurisdiction": "Knowledge Base Dynamic Chunk",
                "effective_year": "2026",
                "clause": f"Chunk {chunk['chunk_id']} ({src}) words {chunk['start_word']}-{chunk['end_word']}",
                "regulatory_threshold_kgco2_per_kwh": threshold,
                "vector": vector,
                "domain": domain,
                "mandate": mandate,
                "standard_code": standard_code,
                "content": chunk["text"],
                "content_snippet": chunk["text"][:200],
                "source_file": src,
            }
            new_entries.append(entry)

        # Keep base deterministic entries (POL-001..POL-004); drop old chunk entries
        base = [
            c for c in self.knowledge_base
            if not str(c.get("policy_id", "")).startswith("POL-CHUNK-")
        ]
        self.knowledge_base = base + new_entries
        self._build_bm25_index()
        logger.info(
            f"build_hybrid_index: rebuilt index with {len(new_entries)} chunks; "
            f"{len(self.knowledge_base)} total policy entries."
        )

    def reload_knowledge_base(self, knowledge_dir: str = "knowledge_base/") -> int:
        """
        Dynamically re-scans knowledge_base/ and rebuilds the hybrid BM25 + vector index.
        Safe to call after update_knowledge_base.py downloads new policy documents.

        Args:
            knowledge_dir: Path to the knowledge base directory containing .txt files.

        Returns:
            Total number of active policy chunks after reload.
        """
        logger.info(f"reload_knowledge_base: re-scanning '{knowledge_dir}' for updated policy documents...")

        # Drop previously dynamically-loaded KB entries (keep base POL-001..POL-004)
        self.knowledge_base = [
            c for c in self.knowledge_base
            if str(c.get("policy_id", "")).startswith("POL-00")
        ]

        # Re-ingest .txt files from directory (one entry per file)
        self.load_knowledge_base_from_dir(knowledge_dir)

        # Also apply sliding-window chunking for richer retrieval granularity
        chunks = self.chunk_text_documents(knowledge_dir=knowledge_dir)
        if chunks:
            self.build_hybrid_index(chunks)
        else:
            self._build_bm25_index()

        total = len(self.knowledge_base)
        logger.info(f"reload_knowledge_base: complete — {total} active policy chunks in hybrid index.")
        return total

    def render_prompt(self, context: Dict[str, Any], prompt_path: str = "prompts/policy_agent.j2") -> str:
        """Renders the Agent 3 Jinja prompt template with runtime variables."""
        import jinja2
        resolved_path = prompt_path
        if not os.path.exists(resolved_path):
            alt1 = os.path.join(os.path.dirname(__file__), "..", prompt_path)
            alt2 = os.path.join("Carbon_Tax_Credits-main", prompt_path)
            if os.path.exists(alt1):
                resolved_path = alt1
            elif os.path.exists(alt2):
                resolved_path = alt2

        if os.path.exists(resolved_path):
            with open(resolved_path, "r", encoding="utf-8") as f:
                template = jinja2.Template(f.read())
            return template.render(**context)
        return ""

    @staticmethod
    def compute_cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
        """
        Formulation 1: Cosine Similarity Vector Search Math
        Score(q, p) = (v_q . v_p) / (||v_q|| * ||v_p||)
        """
        if not vec_a or not vec_b or len(vec_a) != len(vec_b):
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = math.sqrt(sum(a * a for a in vec_a))
        norm_b = math.sqrt(sum(b * b for b in vec_b))

        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0

        return float(dot_product / (norm_a * norm_b))

    def hybrid_search(
        self,
        query_text: Optional[str] = None,
        query_vector: Optional[List[float]] = None,
        top_k: int = 5,
        alpha: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """
        Formulation 4: Hybrid Search Engine combining:
        1. Semantic Vector Cosine Similarity
        2. BM25 Lexical Keyword Scoring
        3. Deterministic Keyword Boosting for Exact Standard Codes & Article Numbers.

        Score_hybrid = alpha * Score_vector + (1 - alpha) * Score_bm25_norm + Score_boost
        """
        effective_alpha = self.alpha if alpha is None else float(alpha)
        bm25_scores = [0.0] * len(self.knowledge_base)

        if query_text and self.bm25:
            q_tokens = self.tokenize(query_text)
            bm25_scores = self.bm25.get_scores(q_tokens)

        max_bm25 = max(bm25_scores) if bm25_scores else 0.0

        ranked_results: List[Dict[str, Any]] = []

        for idx, chunk in enumerate(self.knowledge_base):
            # 1. Cosine similarity score
            vec = chunk.get("vector", [])
            if query_vector is not None and vec:
                vector_score = self.compute_cosine_similarity(query_vector, vec)
            else:
                vector_score = 0.0

            # 2. Normalized BM25 score
            raw_bm25 = bm25_scores[idx] if idx < len(bm25_scores) else 0.0
            bm25_norm = float(raw_bm25 / max_bm25) if max_bm25 > 0.0 else 0.0

            # 3. Exact standard code and article number keyword boosting
            keyword_boost = self.compute_keyword_boost(query_text or "", chunk) if query_text else 0.0

            # 4. Hybrid score combination
            if query_vector is not None and query_text:
                hybrid_score = (effective_alpha * vector_score) + ((1.0 - effective_alpha) * bm25_norm) + keyword_boost
            elif query_vector is not None:
                hybrid_score = vector_score
            elif query_text:
                hybrid_score = bm25_norm + keyword_boost
            else:
                hybrid_score = 0.0

            ranked_results.append({
                "chunk": chunk,
                "policy_id": chunk.get("policy_id"),
                "policy_name": chunk.get("policy_name"),
                "hybrid_score": round(float(hybrid_score), 6),
                "vector_score": round(float(vector_score), 6),
                "bm25_score": round(float(raw_bm25), 6),
                "bm25_norm": round(float(bm25_norm), 6),
                "keyword_boost": round(float(keyword_boost), 6),
            })

        # Rank descending by hybrid score, tie-break by vector score then bm25
        ranked_results.sort(
            key=lambda x: (x["hybrid_score"], x["vector_score"], x["bm25_norm"]),
            reverse=True,
        )

        return ranked_results[:top_k]

    def retrieve_best_policy_chunk(
        self,
        query_vector: Optional[List[float]] = None,
        query_text: Optional[str] = None,
        alpha: Optional[float] = None,
    ) -> Tuple[Optional[Dict[str, Any]], float]:
        """
        Retrieves policy chunk p* from knowledge base that maximizes hybrid score
        combining semantic vector cosine similarity and BM25 keyword scoring with exact code boosting.
        """
        results = self.hybrid_search(
            query_text=query_text,
            query_vector=query_vector,
            top_k=1,
            alpha=alpha,
        )
        if not results:
            return None, 0.0

        best = results[0]
        score = best["hybrid_score"] if query_text else best["vector_score"]

        best_chunk = dict(best["chunk"])
        best_chunk["_retrieval_meta"] = {
            "hybrid_score": best["hybrid_score"],
            "vector_score": best["vector_score"],
            "bm25_score": best["bm25_score"],
            "bm25_norm": best["bm25_norm"],
            "keyword_boost": best["keyword_boost"],
        }

        return best_chunk, score

    def evaluate_line_compliance(
        self,
        line_code: str,
        emission_intensity_kgco2_per_kwh: float,
        data_status: str = "ESTIMATED_PROXY",
        verification_status: str = "UNVERIFIED",
        query_vector: Optional[List[float]] = None,
        query_text: Optional[str] = None,
        upstream_record: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Evaluates legal & environmental compliance for a production line operational context
        using Hybrid RAG search (Vector + BM25 + Exact Keyword Boosting).
        """
        # Formulate query vector q if not explicitly provided
        if not query_vector:
            query_vector = [
                float(emission_intensity_kgco2_per_kwh),
                0.80,
                0.88,
                0.75,
            ]

        # Step 1: Hybrid Semantic + BM25 Vector Search (RAG Retrieval)
        best_policy, retrieval_score = self.retrieve_best_policy_chunk(
            query_vector=query_vector,
            query_text=query_text,
        )

        retrieval_meta = best_policy.get("_retrieval_meta", {}) if best_policy else {}
        cosine_score = float(retrieval_meta.get("vector_score", retrieval_score))
        hybrid_score = float(retrieval_meta.get("hybrid_score", retrieval_score))
        bm25_score = float(retrieval_meta.get("bm25_score", 0.0))
        keyword_boost = float(retrieval_meta.get("keyword_boost", 0.0))

        policy_id = best_policy["policy_id"] if best_policy else "POL-NONE"
        policy_name = best_policy["policy_name"] if best_policy else "Unknown Policy"
        clause = best_policy["clause"] if best_policy else "N/A"
        effective_year = best_policy.get("effective_year", "N/A") if best_policy else "N/A"
        regulatory_threshold = best_policy.get("regulatory_threshold_kgco2_per_kwh", 0.750) if best_policy else 0.750
        verification_mandate = best_policy.get("mandate", "INSPECTION_REQUIRED") if best_policy else "INSPECTION_REQUIRED"

        # Step 2 & Execution Guardrails
        effective_guard_score = hybrid_score if query_text else cosine_score
        # Rule 5: If score drops below guard threshold -> OUT_OF_DOMAIN_POLICY & manual legal review flag
        if effective_guard_score < self.cosine_threshold_guard or not best_policy:
            compliance_status = "OUT_OF_DOMAIN_POLICY"
            manual_legal_review_required = True
        # Rule 1: Data status is 'ESTIMATED_PROXY' or 'REQUIRES_PLANT_SPECIFIC_VERIFICATION' -> PENDING_AUDIT
        elif data_status in ["ESTIMATED_PROXY", "REQUIRES_PLANT_SPECIFIC_VERIFICATION"]:
            compliance_status = "PENDING_AUDIT"
            manual_legal_review_required = False
        else:
            # Formulation 5: Deterministic Compliance Boolean Gate
            # Compliance_Status = PASS if (Emission_Intensity <= Threshold) AND (Verification_Status == 'VERIFIED')
            # else FLAGGED_REQUIRES_EXTERNAL_AUDIT
            if (emission_intensity_kgco2_per_kwh <= regulatory_threshold) and (verification_status == "VERIFIED"):
                compliance_status = "PASS"
                manual_legal_review_required = False
            else:
                compliance_status = "FLAGGED_REQUIRES_EXTERNAL_AUDIT"
                manual_legal_review_required = False

        # Step 3: Formulation 6: Confidence Score Assignment
        # Confidence_Score = min(0.95, Score(q, p*)) * Data_Reliability_Factor
        if data_status == "DIRECT_METERED" and verification_status == "VERIFIED":
            reliability_factor = 1.0
        elif data_status == "ESTIMATED_PROXY":
            reliability_factor = 0.45
        else:
            reliability_factor = 0.60

        eval_score_for_confidence = min(1.0, cosine_score if not query_text else hybrid_score)
        confidence_score = min(0.95, float(eval_score_for_confidence)) * reliability_factor

        # Rule 2: Citation Metadata to prevent legal hallucination
        citation = {
            "source_document": policy_name,
            "policy_id": policy_id,
            "clause": clause,
            "effective_year": effective_year,
            "regulatory_threshold_kgco2_per_kwh": regulatory_threshold,
        }

        # Rule 4: Absolute Traceability linking upstream Carbon_Emission metrics to downstream Tax_Incentive_Screening targets
        traceability = {
            "upstream_source": "Carbon_Emission.csv",
            "line_code": line_code,
            "emission_intensity_kgco2_per_kwh": round(emission_intensity_kgco2_per_kwh, 6),
            "data_status": data_status,
            "verification_status": verification_status,
            "downstream_target": "Tax_Incentive_Screening.csv",
        }

        # Rule 3: Strict Parsable JSON Schema Output with hybrid score telemetry
        return {
            "line_code": line_code,
            "retrieved_policy_id": policy_id,
            "policy_citation": citation,
            "cosine_similarity_score": round(cosine_score, 6),
            "hybrid_score": round(hybrid_score, 6),
            "bm25_score": round(bm25_score, 6),
            "keyword_boost": round(keyword_boost, 6),
            "compliance_status": compliance_status,
            "verification_mandate": verification_mandate,
            "confidence_score": round(confidence_score, 6),
            "manual_legal_review_required": manual_legal_review_required,
            "traceability": traceability,
        }

    def process_emission_records(
        self,
        emission_records: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Ingest emission metrics from Agent 1 (Carbon_Emission.csv or pipeline memory),
        group by production line, and compute RAG policy compliance evaluation.
        """
        if not emission_records:
            return []

        if pd is not None:
            df = pd.DataFrame(emission_records)
            if "line_code" not in df.columns:
                raise ValueError("Input emission records must contain 'line_code'.")

            results: List[Dict[str, Any]] = []

            for line, group in df.groupby("line_code"):
                if "emission_intensity_kgco2_per_kwh" in group.columns:
                    avg_intensity = float(group["emission_intensity_kgco2_per_kwh"].mean())
                elif "estimated_co2_kg" in group.columns and "allocated_energy_kwh" in group.columns:
                    tot_co2 = group["estimated_co2_kg"].sum()
                    tot_energy = group["allocated_energy_kwh"].sum()
                    avg_intensity = float(tot_co2 / tot_energy) if tot_energy > 0 else 0.716
                else:
                    avg_intensity = 0.716

                data_status = str(group["data_status"].iloc[0]) if "data_status" in group.columns else "ESTIMATED_PROXY"
                verification_status = str(group["emission_factor_verification_status"].iloc[0]) if "emission_factor_verification_status" in group.columns else "UNVERIFIED"

                eval_res = self.evaluate_line_compliance(
                    line_code=str(line),
                    emission_intensity_kgco2_per_kwh=avg_intensity,
                    data_status=data_status,
                    verification_status=verification_status,
                )
                results.append(eval_res)

            return results
        else:
            # Fallback pure-Python grouping when pandas is not installed
            if not any("line_code" in r for r in emission_records):
                raise ValueError("Input emission records must contain 'line_code'.")

            grouped: Dict[str, List[Dict[str, Any]]] = {}
            for r in emission_records:
                code = str(r.get("line_code", ""))
                grouped.setdefault(code, []).append(r)

            results = []
            for line, rows in sorted(grouped.items()):
                intensities = [float(r["emission_intensity_kgco2_per_kwh"]) for r in rows if "emission_intensity_kgco2_per_kwh" in r]
                if intensities:
                    avg_intensity = sum(intensities) / len(intensities)
                else:
                    tot_co2 = sum(float(r.get("estimated_co2_kg", 0.0)) for r in rows)
                    tot_energy = sum(float(r.get("allocated_energy_kwh", 0.0)) for r in rows)
                    avg_intensity = float(tot_co2 / tot_energy) if tot_energy > 0 else 0.716

                data_status = str(rows[0].get("data_status", "ESTIMATED_PROXY"))
                verification_status = str(rows[0].get("emission_factor_verification_status", "UNVERIFIED"))

                eval_res = self.evaluate_line_compliance(
                    line_code=str(line),
                    emission_intensity_kgco2_per_kwh=avg_intensity,
                    data_status=data_status,
                    verification_status=verification_status,
                )
                results.append(eval_res)

            return results

    def run_pipeline(
        self,
        emission_input: Union[str, List[Dict[str, Any]]],
        output_json_path: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        End-to-end RAG compliance pipeline taking Agent 1 emission records or file path.
        """
        if isinstance(emission_input, str):
            logger.info(f"Agent 3 (Hybrid RAG): Ingesting emission logs from CSV file: {emission_input}")
            if pd is not None:
                df = pd.read_csv(emission_input)
                records = df.to_dict(orient="records")
            else:
                import csv
                with open(emission_input, "r", encoding="utf-8") as f:
                    records = list(csv.DictReader(f))
        else:
            logger.info(f"Agent 3 (Hybrid RAG): Ingesting {len(emission_input)} emission records directly from pipeline memory.")
            records = emission_input

        results = self.process_emission_records(records)

        if output_json_path:
            logger.info(f"Agent 3 (Hybrid RAG): Exporting verified compliance JSON logs to: {output_json_path}")
            with open(output_json_path, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2)

        return results
