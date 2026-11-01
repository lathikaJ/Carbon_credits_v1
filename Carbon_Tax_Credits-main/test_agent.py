"""
Unit & Integration Test Suite (test_agent.py)
=============================================
Comprehensive automated test suite covering all 5 agents and multi-agent pipeline,
with specialized in-depth verification of Agent 3's Hybrid Search Engine:
1. BM25 Lexical Keyword Scoring
2. Semantic Vector Cosine Similarity
3. Exact Standard Code Boosting (e.g., CEA Grid Baseline v4, ISO 14064-1)
4. Standard Article/Clause/Annex Number Boosting (e.g., Section 4.1, Clause 12b, Annex III)
5. Outranking Vector Distractors with Hybrid Retrieval
6. Dynamic Knowledge Base File Ingestion & BM25 Corpus Indexing
7. Compliance Boolean Gates & Guardrails
8. End-to-End Multi-Agent Pipeline Execution

Usage:
  python test_agent.py
"""

import sys
import os
import unittest
import math
from typing import Dict, List, Any

# Ensure project directories are in sys.path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SUBDIR = os.path.join(CURRENT_DIR, "Carbon_Tax_Credits-main")
for d in [CURRENT_DIR, SUBDIR]:
    if d not in sys.path and os.path.exists(d):
        sys.path.insert(0, d)

from agents.policy_compliance_agent import PolicyComplianceAgent, POLICY_KNOWLEDGE_BASE
from agents.emission_assessment_agent import EmissionAssessmentAgent
from agents.carbon_credit_assessment_agent import CarbonCreditAssessmentAgent
from agents.tax_incentive_agent import TaxIncentiveAgent
from agents.report_generation_agent import ReportGenerationAgent
from agents.pipeline import AgentPipeline
from rank_bm25 import BM25Okapi


class TestPolicyComplianceHybridRAG(unittest.TestCase):
    """
    Agent 3 Test Suite: Hybrid Search Engine, BM25 Keyword Scoring, Exact Code Boosting.
    """

    def setUp(self):
        # Resolve knowledge_base directory path safely
        kb_dir = os.path.join(CURRENT_DIR, "knowledge_base")
        if not os.path.exists(kb_dir):
            kb_dir = os.path.join(SUBDIR, "knowledge_base")
        self.agent = PolicyComplianceAgent(knowledge_dir=kb_dir)

    def test_01_bm25_index_built_successfully(self):
        """Verify BM25 index is automatically constructed across all policy chunks."""
        self.assertIsNotNone(self.agent.bm25)
        self.assertGreaterEqual(len(self.agent.knowledge_base), 4)
        self.assertEqual(len(self.agent.corpus_tokens), len(self.agent.knowledge_base))

    def test_02_cosine_similarity_math(self):
        """Verify mathematical formulation of vector cosine similarity."""
        vec_a = [1.0, 0.0, 0.0]
        vec_b = [1.0, 0.0, 0.0]
        self.assertAlmostEqual(self.agent.compute_cosine_similarity(vec_a, vec_b), 1.0, places=5)

        vec_c = [0.0, 1.0, 0.0]
        self.assertAlmostEqual(self.agent.compute_cosine_similarity(vec_a, vec_c), 0.0, places=5)

        # Mismatched lengths or empty vectors return 0.0 safely
        self.assertEqual(self.agent.compute_cosine_similarity([], [1.0]), 0.0)
        self.assertEqual(self.agent.compute_cosine_similarity([1.0, 2.0], [1.0]), 0.0)

    def test_03_hybrid_retrieval_combines_vector_and_bm25(self):
        """Verify hybrid scoring formula: Score = alpha * S_vec + (1 - alpha) * S_bm25 + S_boost."""
        query_text = "grid emission baseline"
        query_vector = [0.716, 0.85, 0.90, 0.80]

        results = self.agent.hybrid_search(
            query_text=query_text,
            query_vector=query_vector,
            top_k=3,
            alpha=0.5,
        )
        self.assertGreater(len(results), 0)
        top = results[0]
        self.assertIn("hybrid_score", top)
        self.assertIn("vector_score", top)
        self.assertIn("bm25_score", top)
        self.assertIn("keyword_boost", top)
        self.assertGreater(top["hybrid_score"], 0.0)

    def test_04_exact_keyword_boosting_cea_grid_baseline_v4(self):
        """
        CRITICAL REQUIREMENT 3:
        Verify exact standard code 'CEA Grid Baseline v4' receives keyword boosting
        and outranks high-similarity vector distractor matches.
        """
        # Vector identical to POL-004 (ISO 14064-1), which has vector cosine similarity = 1.0
        iso_distractor_vector = [0.716, 0.80, 0.88, 0.75]

        # In pure vector search, POL-004 wins with score 1.0
        chunk_pure_vec, score_pure_vec = self.agent.retrieve_best_policy_chunk(
            query_vector=iso_distractor_vector
        )
        self.assertEqual(chunk_pure_vec["policy_id"], "POL-004")
        self.assertAlmostEqual(score_pure_vec, 1.0, places=3)

        # In HYBRID search with exact keyword query 'CEA Grid Baseline v4':
        # The exact standard code boosting must elevate the CEA Grid Baseline chunk above POL-004
        results = self.agent.hybrid_search(
            query_text="CEA Grid Baseline v4",
            query_vector=iso_distractor_vector,
            top_k=5,
        )
        top_result = results[0]

        # Verify keyword boost was awarded
        self.assertGreater(top_result["keyword_boost"], 0.0)

        # Verify the top retrieved chunk is a CEA Grid Baseline document
        top_policy_name = top_result["policy_name"].upper()
        top_policy_id = top_result["policy_id"]
        is_cea = ("CEA" in top_policy_name or "GRID BASELINE" in top_policy_name or top_policy_id in ["POL-001", "POL-KB-006"])
        self.assertTrue(is_cea, f"Expected CEA Grid Baseline to win, got {top_result}")

        # Verify hybrid score decisively outranked the distractor
        distractor_hybrid_score = next(r["hybrid_score"] for r in results if r["policy_id"] == "POL-004")
        self.assertGreater(top_result["hybrid_score"], distractor_hybrid_score)

    def test_05_exact_article_number_boosting_section_4_1(self):
        """
        Verify that exact standard article number 'Section 4.1' receives keyword boosting
        and retrieves Section 4.1 regulatory baseline chunks.
        """
        results = self.agent.hybrid_search(query_text="Section 4.1 Grid OM Baseline", top_k=3)
        self.assertGreater(len(results), 0)
        top = results[0]

        self.assertGreater(top["keyword_boost"], 0.0)
        self.assertIn(top["policy_id"], ["POL-001", "POL-KB-006"])
        self.assertTrue("4.1" in top["chunk"]["clause"] or "4.1" in top["chunk"].get("content", ""))

    def test_06_exact_clause_number_boosting_clause_12b(self):
        """
        Verify that exact clause number 'Clause 12b' receives keyword boosting
        and retrieves Clause 12b production intensity limits.
        """
        results = self.agent.hybrid_search(query_text="Clause 12b Production Intensity Limits", top_k=3)
        self.assertGreater(len(results), 0)
        top = results[0]

        self.assertGreater(top["keyword_boost"], 0.0)
        self.assertIn(top["policy_id"], ["POL-002", "POL-KB-007"])
        self.assertTrue("12b" in top["chunk"]["clause"].lower() or "12b" in top["chunk"].get("content", "").lower())

    def test_07_exact_annex_boosting_annex_iii(self):
        """
        Verify that exact standard annex 'Annex III' receives keyword boosting
        and retrieves Verra / CDM carbon credit methodology rules.
        """
        results = self.agent.hybrid_search(query_text="Annex III Additionality MRV", top_k=3)
        self.assertGreater(len(results), 0)
        top = results[0]

        self.assertGreater(top["keyword_boost"], 0.0)
        self.assertIn(top["policy_id"], ["POL-003", "POL-KB-005"])
        self.assertTrue("annex iii" in top["chunk"]["clause"].lower() or "annex iii" in top["chunk"].get("content", "").lower())

    def test_08_exact_standard_code_iso_14064_1(self):
        """
        Verify that standard code 'ISO 14064-1 Section 6.2' receives boosting and retrieves POL-004.
        """
        results = self.agent.hybrid_search(query_text="ISO 14064-1 Section 6.2 Data Reliability", top_k=3)
        self.assertGreater(len(results), 0)
        top = results[0]

        self.assertGreater(top["keyword_boost"], 0.0)
        self.assertEqual(top["policy_id"], "POL-004")

    def test_09_dynamic_knowledge_base_dir_ingestion(self):
        """Verify dynamic scanning and ingestion of .txt documents from knowledge_base/ directory."""
        kb_files = [c for c in self.agent.knowledge_base if str(c.get("policy_id", "")).startswith("POL-KB-")]
        self.assertGreaterEqual(len(kb_files), 3)

        # Verify CEA document ref was indexed
        results = self.agent.hybrid_search(query_text="Document Ref: CEA-EF-2026-V1.4", top_k=1)
        self.assertGreater(len(results), 0)
        self.assertIn(results[0]["policy_id"], ["POL-KB-006", "POL-001"])

    def test_10_evaluate_line_compliance_output_schema(self):
        """
        Verify strict output schema of evaluate_line_compliance including hybrid score telemetry.
        """
        res = self.agent.evaluate_line_compliance(
            line_code="M5L011",
            emission_intensity_kgco2_per_kwh=0.716,
            data_status="ESTIMATED_PROXY",
            verification_status="UNVERIFIED",
            query_text="CEA Grid Baseline v4",
        )

        expected_keys = [
            "line_code",
            "retrieved_policy_id",
            "policy_citation",
            "cosine_similarity_score",
            "hybrid_score",
            "bm25_score",
            "keyword_boost",
            "compliance_status",
            "verification_mandate",
            "confidence_score",
            "manual_legal_review_required",
            "traceability",
        ]
        for key in expected_keys:
            self.assertIn(key, res)

        self.assertEqual(res["line_code"], "M5L011")
        self.assertEqual(res["compliance_status"], "PENDING_AUDIT")
        self.assertGreater(res["keyword_boost"], 0.0)
        self.assertIn("CEA", res["policy_citation"]["source_document"].upper())

    def test_11_compliance_boolean_gates(self):
        """
        Verify deterministic boolean compliance gates:
        1. PASS: intensity <= threshold AND VERIFIED.
        2. FLAGGED_REQUIRES_EXTERNAL_AUDIT: intensity > threshold OR UNVERIFIED.
        3. PENDING_AUDIT: ESTIMATED_PROXY.
        """
        # Case 1: Direct metered & verified <= threshold -> PASS
        pass_res = self.agent.evaluate_line_compliance(
            line_code="L1",
            emission_intensity_kgco2_per_kwh=0.710,
            data_status="DIRECT_METERED",
            verification_status="VERIFIED",
        )
        self.assertEqual(pass_res["compliance_status"], "PASS")

        # Case 2: Exceeding threshold -> FLAGGED_REQUIRES_EXTERNAL_AUDIT
        fail_res = self.agent.evaluate_line_compliance(
            line_code="L2",
            emission_intensity_kgco2_per_kwh=0.950,
            data_status="DIRECT_METERED",
            verification_status="VERIFIED",
        )
        self.assertEqual(fail_res["compliance_status"], "FLAGGED_REQUIRES_EXTERNAL_AUDIT")

        # Case 3: Proxy data -> PENDING_AUDIT
        proxy_res = self.agent.evaluate_line_compliance(
            line_code="L3",
            emission_intensity_kgco2_per_kwh=0.710,
            data_status="ESTIMATED_PROXY",
            verification_status="VERIFIED",
        )
        self.assertEqual(proxy_res["compliance_status"], "PENDING_AUDIT")

    def test_12_out_of_domain_policy_guardrail(self):
        """
        Verify Rule 5: If retrieval similarity drops below 0.70,
        flag context as 'OUT_OF_DOMAIN_POLICY' and require manual legal review.
        """
        orthogonal_vec = [0.0, 0.0, 0.0, 0.0]
        res = self.agent.evaluate_line_compliance(
            line_code="L_OUT",
            emission_intensity_kgco2_per_kwh=0.0,
            data_status="DIRECT_METERED",
            verification_status="VERIFIED",
            query_vector=orthogonal_vec,
        )
        self.assertEqual(res["compliance_status"], "OUT_OF_DOMAIN_POLICY")
        self.assertTrue(res["manual_legal_review_required"])

    def test_13_alpha_weight_parameter_behavior(self):
        """Verify alpha parameter allows switching between pure vector, balanced, and pure BM25."""
        vec = [0.716, 0.85, 0.90, 0.80]
        text = "green tax capital allowances"

        res_vec = self.agent.hybrid_search(query_text=text, query_vector=vec, alpha=1.0)
        res_bm25 = self.agent.hybrid_search(query_text=text, query_vector=vec, alpha=0.0)

        self.assertNotEqual(res_vec[0]["hybrid_score"], res_bm25[0]["hybrid_score"])


class TestEmissionAssessmentAgent(unittest.TestCase):
    """
    Agent 1 Test Suite: Telemetry GHG calculation & unmetered proxy guardrails.
    """

    def setUp(self):
        self.agent = EmissionAssessmentAgent()

    def test_14_weighted_allocation_and_co2_math(self):
        """Verify weighted energy allocation share formula and safe division."""
        alloc = self.agent.calculate_weighted_allocation(
            runtime_hours=20.0,
            h_total=100.0,
            actual_qty=200.0,
            sum_qty=1000.0,
            oee_pct=80.0,
            sum_oee=400.0,
        )
        expected_w = 0.40 * 0.20 + 0.35 * 0.20 + 0.25 * 0.20
        self.assertAlmostEqual(alloc["allocation_weight"], expected_w, places=4)

        # Test safe_divide handles zero division gracefully
        self.assertEqual(self.agent.safe_divide(100.0, 0.0), 0.0)

    def test_15_unmetered_proxy_guardrail_cap(self):
        """Verify unmetered telemetry confidence cap at <= 0.45."""
        self.assertEqual(self.agent.CONFIDENCE_CAP_UNMETERED, 0.45)
        self.assertEqual(self.agent.DEFAULT_GRID_EF, 0.716)


class TestCarbonCreditAssessmentAgent(unittest.TestCase):
    """
    Agent 2 Test Suite: 7-day baseline & potential carbon credits quantification.
    """

    def setUp(self):
        self.agent = CarbonCreditAssessmentAgent()

    def test_16_baseline_and_potential_credits_math(self):
        """Verify 7-day initial operating baseline calculation and screening."""
        records = [{"estimated_co2_kg": 100.0, "date": f"2026-07-0{i+1}"} for i in range(7)]
        baseline = self.agent.calculate_line_baseline(records)
        self.assertAlmostEqual(baseline, 100.0, places=4)

        eval_res = self.agent.evaluate_line_credit_eligibility(
            line_code="M5L011",
            emission_records=records,
        )
        self.assertIn("potential_credit_quantity", eval_res)
        self.assertIn("eligibility_screen", eval_res)

    def test_17_negative_reduction_defaults_to_zero(self):
        """Verify potential credits do not award negative reductions."""
        # Current emission higher than baseline (150 > 100) -> 0 credit quantity
        records = [
            {"estimated_co2_kg": 100.0, "date": "2026-07-01"},
            {"estimated_co2_kg": 100.0, "date": "2026-07-02"},
            {"estimated_co2_kg": 100.0, "date": "2026-07-03"},
            {"estimated_co2_kg": 100.0, "date": "2026-07-04"},
            {"estimated_co2_kg": 100.0, "date": "2026-07-05"},
            {"estimated_co2_kg": 100.0, "date": "2026-07-06"},
            {"estimated_co2_kg": 100.0, "date": "2026-07-07"},
            {"estimated_co2_kg": 150.0, "date": "2026-07-08"},
        ]
        eval_res = self.agent.evaluate_line_credit_eligibility(
            line_code="M5L011",
            emission_records=records,
        )
        self.assertEqual(eval_res["potential_credit_quantity"], 0.0)


class TestTaxIncentiveAgent(unittest.TestCase):
    """
    Agent 4 Test Suite: Green tax rebate optimization & eligibility screening.
    """

    def setUp(self):
        self.agent = TaxIncentiveAgent()

    def test_18_tax_incentive_screening_eligibility(self):
        """Verify candidate qualification gate: OEE >= 80% AND CI < threshold."""
        # Qualified candidate
        res_pass = self.agent.evaluate_line_incentive_eligibility(
            line_code="L_QUAL",
            avg_oee_pct=85.0,
            co2_per_product_kg=0.350,
            plant_location="Tamil Nadu",
        )
        self.assertEqual(res_pass["eligibility_screen"], "CANDIDATE_FOR_REVIEW")
        self.assertEqual(res_pass["jurisdiction_status"], "CONFIRMED")

        # Disqualified on low OEE and missing location
        res_fail = self.agent.evaluate_line_incentive_eligibility(
            line_code="L_DISQ",
            avg_oee_pct=72.0,
            co2_per_product_kg=0.350,
            plant_location="UNKNOWN",
        )
        self.assertEqual(res_fail["eligibility_screen"], "NOT_FLAGGED")
        self.assertEqual(res_fail["jurisdiction_status"], "REQUIRES_LOCATION_CONFIRMATION")


class TestReportGenerationAgent(unittest.TestCase):
    """
    Agent 5 Test Suite: Composite confidence score & executive report synthesis.
    """

    def setUp(self):
        self.agent = ReportGenerationAgent()

    def test_19_composite_confidence_score_formula(self):
        """Verify composite confidence score formula capped at 0.45 for unmetered data."""
        conf, level = self.agent.calculate_composite_confidence(
            confidence_energy=0.90,
            confidence_production=0.90,
            confidence_policy=0.90,
            is_metered=False,
        )
        self.assertEqual(conf, 0.45)
        self.assertEqual(level, "LOW")

        # Metered data allows full score
        conf_metered, level_metered = self.agent.calculate_composite_confidence(
            confidence_energy=0.90,
            confidence_production=0.90,
            confidence_policy=0.90,
            is_metered=True,
        )
        self.assertAlmostEqual(conf_metered, 0.90, places=2)
        self.assertEqual(level_metered, "HIGH")


class TestAgentPipelineIntegration(unittest.TestCase):
    """
    End-to-End Multi-Agent Pipeline Sequential Execution Test.
    """

    def test_20_pipeline_orchestration(self):
        """Verify AgentPipeline initialises and coordinates all 5 stages."""
        pipeline = AgentPipeline()
        self.assertIsNotNone(pipeline.emission_agent)
        self.assertIsNotNone(pipeline.credit_agent)
        self.assertIsNotNone(pipeline.policy_agent)
        self.assertIsNotNone(pipeline.tax_agent)
        self.assertIsNotNone(pipeline.report_agent)


class TestKnowledgeBasePipeline(unittest.TestCase):
    """
    Tests 21-23: PDF extraction, deduplication hash checking, and dynamic re-indexing
    for the automated policy knowledge base pipeline.
    """

    def test_21_pdf_text_extraction(self):
        """
        Verify extract_text_from_pdf() returns a non-empty string from a minimal
        PDF byte sequence.  The raw-stream regex fallback embedded in parser.py
        must catch the Tj operator and surface the embedded text token.
        """
        import tempfile

        # Minimal syntactically-valid PDF containing a visible text string via Tj
        mock_pdf = (
            b"%PDF-1.4\n"
            b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
            b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
            b"3 0 obj\n<< /Type /Page /MediaBox [0 0 612 792] /Contents 4 0 R /Parent 2 0 R >>\nendobj\n"
            b"4 0 obj\n<< /Length 55 >>\nstream\n"
            b"BT /F1 12 Tf 72 720 Td (CEA Grid Baseline Carbon Policy) Tj ET\n"
            b"endstream\nendobj\n"
            b"xref\n0 5\n"
            b"0000000000 65535 f \n"
            b"0000000009 00000 n \n"
            b"0000000062 00000 n \n"
            b"0000000119 00000 n \n"
            b"0000000218 00000 n \n"
            b"trailer\n<< /Size 5 /Root 1 0 R >>\n"
            b"startxref\n328\n%%EOF\n"
        )

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(mock_pdf)
            tmp_path = tmp.name

        try:
            from knowledge_base.parser import extract_text_from_pdf
            text = extract_text_from_pdf(tmp_path)
            self.assertIsInstance(text, str, "extract_text_from_pdf must return a str")
            self.assertGreater(len(text), 0, "Extracted text must be non-empty")
            # The Tj stream contains "CEA" — raw fallback should surface it
            self.assertIn("CEA", text.upper(), "Extracted text must contain 'CEA'")
        finally:
            os.unlink(tmp_path)

    def test_22_duplicate_document_hash(self):
        """
        Verify that:
        1. SHA-256 hashes are deterministic (same bytes → same hash).
        2. The hash digest is exactly 64 hex characters.
        3. Different byte content produces a different hash.
        4. A hash that has never been ingested is correctly reported as NOT duplicate.
        """
        from knowledge_base.parser import compute_file_hash, is_duplicate_document

        payload = b"Test policy document content for deduplication check"
        h1 = compute_file_hash(payload)
        h2 = compute_file_hash(payload)

        # Determinism
        self.assertEqual(h1, h2, "Same bytes must always yield the same SHA-256 hash")
        # Length: SHA-256 hex digest = 64 chars
        self.assertEqual(len(h1), 64, "SHA-256 hex digest must be 64 characters long")
        # Hex characters only
        self.assertTrue(all(c in "0123456789abcdef" for c in h1), "Hash must be lowercase hex")

        # Distinct content → distinct hash
        h3 = compute_file_hash(b"Completely different content - green tax rebate OEE benchmark")
        self.assertNotEqual(h1, h3, "Different content must produce a different hash")

        # Unknown hash must not be flagged as duplicate (no lineage DB pre-populated)
        is_dup = is_duplicate_document("nonexistent_hash_abc123_xyz_not_in_any_registry")
        self.assertFalse(is_dup, "An unknown hash must be reported as NOT duplicate")

    def test_23_knowledge_base_reindex(self):
        """
        Verify that PolicyComplianceAgent.reload_knowledge_base() dynamically
        picks up a newly written .txt file and expands the hybrid index count.
        The subsequent hybrid_search() must return at least one result.
        """
        kb_dir = os.path.join(CURRENT_DIR, "knowledge_base")
        if not os.path.exists(kb_dir):
            kb_dir = os.path.join(SUBDIR, "knowledge_base")

        agent = PolicyComplianceAgent(knowledge_dir=kb_dir)
        initial_count = len(agent.knowledge_base)

        tmp_file = os.path.join(kb_dir, "_test_tmp_reindex_policy.txt")
        try:
            with open(tmp_file, "w", encoding="utf-8") as f:
                f.write(
                    "TEST TEMPORARY POLICY DOCUMENT\n"
                    "Document Ref: TEST-POL-REINDEX-001 | Jurisdiction: Test Environment\n"
                    "Section 1.0 Carbon Threshold Reindex Verification\n"
                    "This document verifies dynamic reindexing. "
                    "Threshold: 0.750 kg CO2/kWh. OEE benchmark 85 percent.\n"
                )

            new_count = agent.reload_knowledge_base(knowledge_dir=kb_dir)
            self.assertGreater(
                new_count, initial_count,
                f"reload_knowledge_base() must increase chunk count (was {initial_count}, got {new_count})"
            )

            # Hybrid search must surface the new document
            results = agent.hybrid_search(
                query_text="test policy carbon threshold reindex",
                top_k=10,
            )
            self.assertGreater(len(results), 0, "hybrid_search must return at least one result after reindex")

        finally:
            if os.path.exists(tmp_file):
                os.unlink(tmp_file)


if __name__ == "__main__":
    unittest.main(verbosity=2)
