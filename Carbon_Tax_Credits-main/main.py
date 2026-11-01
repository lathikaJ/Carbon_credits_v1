"""
Main Framework Orchestrator
===========================
Top-level entry point connecting all multi-agent pipelines:
1. Loads environment variables (.env) & LLMService.
2. Runs Knowledge Base Downloader & Loader (download_knowledge_base.py).
3. Executes 5-Stage Multi-Agent Industrial Carbon Assessment Pipeline:
   - Stage 1: Emission Assessment Agent
   - Stage 2: Carbon Credit Assessment Agent
   - Stage 3: Policy & Compliance Agent (RAG)
   - Stage 4: Tax Incentive Optimization Agent
   - Stage 5: Report Generation Agent
4. Exports structured JSON payloads & Markdown executive summary.
5. Automatically syncs output payloads to ecopulse-executive-main/public/data/ for the frontend dashboard.

Usage:
  python main.py [--grid-ef 0.716] [--prod input_data/Production.csv] [--energy input_data/Energy_Estimated_Proxy.csv]
"""

import os
import sys
import shutil
import json
import argparse
import logging
from typing import Dict, Any

from llm_service import LLMService
from download_knowledge_base import create_default_documents, load_pdfs_to_text
from agents.pipeline import AgentPipeline

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("MainOrchestrator")


def sync_frontend_data(output_dir: str = "frontend/public/data"):
    """
    Copies backend JSON outputs and executive summary Markdown into the frontend public/data directory.
    """
    os.makedirs(output_dir, exist_ok=True)
    files_to_sync = [
        "emission_assessment_output.json",
        "carbon_credit_assessment_output.json",
        "policy_compliance_output.json",
        "tax_incentive_output.json",
        "executive_report_output.json",
        "executive_summary.md",
    ]

    synced_count = 0
    for filename in files_to_sync:
        if os.path.exists(filename):
            target_path = os.path.join(output_dir, filename)
            shutil.copy2(filename, target_path)
            synced_count += 1

    logger.info(f"Frontend Data Sync: Synced {synced_count} backend output payload(s) to '{output_dir}'.")


def run_pipeline(
    grid_emission_factor: float = 0.716,
    production_csv: str = "input_data/Production.csv",
    energy_csv: str = "input_data/Energy_Estimated_Proxy.csv",
    dashboard_kpi_csv: str = "input_data/Dashboard_KPI.csv",
    validation_report_csv: str = "input_data/Validation_Report.csv",
    frontend_data_dir: str = "frontend/public/data",
) -> Dict[str, Any]:
    """
    Executes end-to-end multi-agent pipeline and syncs results to frontend dashboard.
    """
    logger.info("==================================================================")
    logger.info("      INDUSTRIAL AI MULTI-AGENT PIPELINE ORCHESTRATOR             ")
    logger.info("==================================================================")

    # 1. Initialize LLM & Environment Service
    llm_service = LLMService(env_file_path=".env", prompts_dir="prompts")

    # 2. Initialize Knowledge Base & Policy Store
    create_default_documents("knowledge_base")
    load_pdfs_to_text("knowledge_base")

    # 3. Instantiate & Run 5-Stage Agent Pipeline
    pipeline = AgentPipeline(grid_emission_factor=grid_emission_factor)
    pipeline_results = pipeline.execute_pipeline(
        production_csv_path=production_csv,
        energy_proxy_csv_path=energy_csv,
        dashboard_kpi_csv_path=dashboard_kpi_csv,
        validation_report_csv_path=validation_report_csv,
        emission_output_json="emission_assessment_output.json",
        credit_output_json="carbon_credit_assessment_output.json",
        policy_output_json="policy_compliance_output.json",
        tax_output_json="tax_incentive_output.json",
        report_output_json="executive_report_output.json",
        report_output_md="executive_summary.md",
    )

    # 4. Sync to Dashboard Frontend
    sync_frontend_data(output_dir=frontend_data_dir)

    logger.info("==================================================================")
    logger.info("        PIPELINE COMPLETED & DASHBOARD DATA SYNCHRONIZED           ")
    logger.info("==================================================================")

    return pipeline_results


def main():
    parser = argparse.ArgumentParser(
        description="Industrial Carbon Credit Assessment & Compliance Multi-Agent Pipeline"
    )
    parser.add_argument("--grid-ef", type=float, default=0.716, help="Grid Emission Factor in kg CO2/kWh")
    parser.add_argument("--prod", type=str, default="input_data/Production.csv", help="Path to Production CSV")
    parser.add_argument("--energy", type=str, default="input_data/Energy_Estimated_Proxy.csv", help="Path to Energy Proxy CSV")
    parser.add_argument("--kpi", type=str, default="input_data/Dashboard_KPI.csv", help="Path to Dashboard KPI CSV")
    parser.add_argument("--val", type=str, default="input_data/Validation_Report.csv", help="Path to Validation Report CSV")
    parser.add_argument("--frontend-dir", type=str, default="frontend/public/data", help="Target dir for frontend data sync")

    args, _ = parser.parse_known_args()  # ignore flags consumed by run_agent.py (e.g. --sync-kb)

    run_pipeline(
        grid_emission_factor=args.grid_ef,
        production_csv=args.prod,
        energy_csv=args.energy,
        dashboard_kpi_csv=args.kpi,
        validation_report_csv=args.val,
        frontend_data_dir=args.frontend_dir,
    )


if __name__ == "__main__":
    main()
