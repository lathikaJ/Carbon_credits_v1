"""
Multi-Agent Industrial AI Pipeline
==================================
Orchestrates sequential 5-stage multi-agent execution for industrial carbon accounting:
Agent 1 (Emission Agent) -> Agent 2 (Carbon Credit Agent) -> Agent 3 (Policy RAG Agent) -> Agent 4 (Tax Incentive Agent) -> Agent 5 (Report Generation Agent)

Data Flow:
- Raw Telemetry (Production, Energy Proxy) -> Agent 1 -> Daily Emission Records
- Daily Emission Records -> Agent 2 -> Carbon Credit Assessments & Compliance Screening
- Daily Emission Records -> Agent 3 (RAG) -> Policy Compliance & Legal Audits
- Daily Emission Records -> Agent 4 -> Tax Incentive Optimization & Financial Allowances
- All Upstream Findings -> Agent 5 -> Final Executive JSON & Markdown Audit Report
"""

import json
import logging
from typing import Dict, List, Any, Optional
from .emission_assessment_agent import EmissionAssessmentAgent
from .carbon_credit_assessment_agent import CarbonCreditAssessmentAgent
from .policy_compliance_agent import PolicyComplianceAgent
from .tax_incentive_agent import TaxIncentiveAgent
from .report_generation_agent import ReportGenerationAgent

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("AgentPipeline")


class AgentPipeline:
    """
    Sequential industrial AI pipeline orchestrator that chains Agent 1 -> Agent 2 -> Agent 3 -> Agent 4 -> Agent 5
    """

    def __init__(
        self,
        grid_emission_factor: float = 0.716,
        confidence_cap_unmetered: float = 0.45,
        confidence_score_screening: float = 0.191,
        cosine_threshold_guard: float = 0.70,
        benchmark_ci_threshold: float = 0.450,
    ):
        self.emission_agent = EmissionAssessmentAgent(
            grid_emission_factor=grid_emission_factor,
            confidence_cap_unmetered=confidence_cap_unmetered,
        )
        self.credit_agent = CarbonCreditAssessmentAgent(
            confidence_score_screening=confidence_score_screening,
        )
        self.policy_agent = PolicyComplianceAgent(
            cosine_threshold_guard=cosine_threshold_guard,
        )
        self.tax_agent = TaxIncentiveAgent(
            benchmark_ci_threshold=benchmark_ci_threshold,
        )
        self.report_agent = ReportGenerationAgent()

    def execute_pipeline(
        self,
        production_csv_path: str,
        energy_proxy_csv_path: str,
        dashboard_kpi_csv_path: Optional[str] = None,
        validation_report_csv_path: Optional[str] = None,
        emission_output_json: Optional[str] = None,
        credit_output_json: Optional[str] = None,
        policy_output_json: Optional[str] = None,
        tax_output_json: Optional[str] = None,
        report_output_json: Optional[str] = None,
        report_output_md: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Executes 5-stage multi-agent pipeline sequentially:
        1. Agent 1 computes daily emissions from raw telemetry.
        2. Agent 1 output is passed directly into Agent 2 to assess baseline emissions & credit eligibility.
        3. Agent 1 output is passed directly into Agent 3 (RAG) to evaluate policy compliance & legal citations.
        4. Agent 1 output is passed directly into Agent 4 to optimize tax incentives & rebate allowances.
        5. Findings from Agents 1-4 are synthesized by Agent 5 into final JSON & Markdown audit reports.
        """
        logger.info("==================================================================")
        logger.info("       STARTING INDUSTRIAL MULTI-AGENT SEQUENTIAL PIPELINE        ")
        logger.info("==================================================================")

        # STAGE 1: AGENT 1 (Emission Assessment Agent)
        logger.info("[STAGE 1] Invoking Agent 1: Emission Assessment Agent...")
        emission_results = self.emission_agent.run_pipeline(
            production_csv_path=production_csv_path,
            energy_proxy_csv_path=energy_proxy_csv_path,
            output_json_path=emission_output_json,
        )
        logger.info(f"[STAGE 1 COMPLETED] Agent 1 generated {len(emission_results)} daily line emission records.")

        # STAGE 2: AGENT 2 (Carbon Credit Assessment Agent)
        logger.info("[STAGE 2] Passing Agent 1 output records as direct input to Agent 2: Carbon Credit Assessment Agent...")
        credit_results = self.credit_agent.run_pipeline(
            emission_input=emission_results,
            output_json_path=credit_output_json,
        )
        logger.info(f"[STAGE 2 COMPLETED] Agent 2 generated {len(credit_results)} carbon credit line assessments.")

        # STAGE 3: AGENT 3 (Policy & Compliance Agent RAG)
        logger.info("[STAGE 3] Passing Agent 1 output records as direct input to Agent 3: Policy & Compliance Agent (RAG)...")
        policy_results = self.policy_agent.run_pipeline(
            emission_input=emission_results,
            output_json_path=policy_output_json,
        )
        logger.info(f"[STAGE 3 COMPLETED] Agent 3 generated {len(policy_results)} RAG policy compliance audits.")

        # STAGE 4: AGENT 4 (Tax Incentive Optimization Agent)
        logger.info("[STAGE 4] Passing Agent 1 output records as direct input to Agent 4: Tax Incentive Optimization Agent...")
        tax_results = self.tax_agent.run_pipeline(
            emission_input=emission_results,
            dashboard_kpi_input=dashboard_kpi_csv_path,
            output_json_path=tax_output_json,
        )
        logger.info(f"[STAGE 4 COMPLETED] Agent 4 generated {len(tax_results)} tax incentive screening evaluations.")

        # STAGE 5: AGENT 5 (Report Generation Agent)
        logger.info("[STAGE 5] Passing all upstream agent outputs to Agent 5: Report Generation Agent...")
        report_results = self.report_agent.run_pipeline(
            agent_1_emissions=emission_results,
            agent_2_credits=credit_results,
            agent_3_policies=policy_results,
            agent_4_taxes=tax_results,
            validation_report_input=validation_report_csv_path,
            output_json_path=report_output_json,
            output_md_path=report_output_md,
        )
        logger.info(f"[STAGE 5 COMPLETED] Agent 5 generated executive report (Composite Confidence Score: {report_results['composite_confidence_score']}).")

        logger.info("==================================================================")
        logger.info("       MULTI-AGENT SEQUENTIAL PIPELINE EXECUTED SUCCESSFULLY       ")
        logger.info("==================================================================")

        return {
            "agent_1_emissions": emission_results,
            "agent_2_credit_assessments": credit_results,
            "agent_3_policy_compliance": policy_results,
            "agent_4_tax_incentives": tax_results,
            "agent_5_executive_report": report_results,
        }

    run_pipeline = execute_pipeline
