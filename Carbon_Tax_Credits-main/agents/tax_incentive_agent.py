"""
Tax Incentive Optimization Agent (Agent 4)
===========================================
An autonomous, deterministic industrial AI component responsible for mapping plant
operational efficiency, carbon intensities, and equipment performance metrics to potential
green tax incentives, government rebates, and financial allowances.

Mathematical Formulations Executed:
1. Financial Optimization Objective Function (Maximize Rebate Benefit F):
   Maximize F = sum_{i} ( Q_i * Rebate_Rate * I(OEE_i >= 85%) * I(CI_i < mu_plant) )
   Subject to operational constraints: sum(Q_i) >= Demand_target AND Downtime_i <= Max_Limit.

2. Incentive Eligibility Gate:
   Eligibility_Screen = CANDIDATE_FOR_REVIEW if (Avg_OEE_pct >= 80.0) AND (Estimated_Carbon_Intensity <= Benchmark_Threshold)
   AND (Verification_Status == 'REQUIRES_EXTERNAL_VERIFICATION') else NOT_FLAGGED.

3. Confidence Score Assignment:
   Tax optimization confidence: Confidence_Score = 0.383 (Default Low for proxy data) or up to 0.85 if sub-metered and independently audited.

Execution Rules & Guardrails:
- Rule 1: Output mandatory disclaimer: "ILLUSTRATIVE SCREENING ONLY -- NOT TAX ADVICE. Flags are based purely on operational KPI thresholds."
- Rule 2: Missing jurisdiction context (plant location 'UNKNOWN') sets status to 'REQUIRES_LOCATION_CONFIRMATION' and blocks automated rebate calculation.
- Rule 3: Output strict JSON schema with 'line_code', 'investment_category', 'technology_category', 'potential_incentive_category', 'eligibility_screen', 'scheme_name', 'confidence_score', and 'disclaimer'.
- Rule 4: Maintain absolute traceability linking upstream Dashboard_KPI metrics to Tax_Incentive_Screening fields.
- Rule 5: If government_scheme_required is True, mark source validation and external tax professional review flags as mandatory.
"""

import math
import json
import logging
from typing import Dict, List, Any, Optional, Tuple, Union
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("TaxIncentiveAgent")


class TaxIncentiveAgent:
    """
    Agent 4: Tax Incentive Optimization Agent
    Maps operational KPIs and carbon metrics to potential green tax incentives and subsidies.
    """

    MANDATORY_DISCLAIMER: str = (
        "ILLUSTRATIVE SCREENING ONLY -- NOT TAX ADVICE. Flags are based purely on operational "
        "KPI thresholds (OEE, energy intensity, downtime) as a starting point for a qualified tax "
        "professional's review. This dataset makes no claim about eligibility under any specific law or scheme."
    )

    DEFAULT_BENCHMARK_CI_THRESHOLD: float = 0.450  # kg CO2/product benchmark threshold
    DEFAULT_REBATE_RATE: float = 0.05  # $0.05 per unit rebate rate

    def __init__(
        self,
        benchmark_ci_threshold: float = DEFAULT_BENCHMARK_CI_THRESHOLD,
        default_rebate_rate: float = DEFAULT_REBATE_RATE,
    ):
        self.benchmark_ci_threshold = float(benchmark_ci_threshold)
        self.default_rebate_rate = float(default_rebate_rate)

    def render_prompt(self, context: Dict[str, Any], prompt_path: str = "prompts/tax_agent.j2") -> str:
        """Renders the Agent 4 Jinja prompt template with runtime variables."""
        import os
        import jinja2
        if os.path.exists(prompt_path):
            with open(prompt_path, "r", encoding="utf-8") as f:
                template = jinja2.Template(f.read())
            return template.render(**context)
        return ""

    @staticmethod
    def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
        """Helper for safe division operations."""
        try:
            if denominator is None or math.isnan(denominator) or denominator == 0:
                return default
            if numerator is None or math.isnan(numerator):
                return default
            return float(numerator / denominator)
        except ZeroDivisionError:
            return default

    def optimize_rebate_objective(
        self,
        line_metrics: List[Dict[str, Any]],
        rebate_rate: Optional[float] = None,
        demand_target: float = 0.0,
        max_downtime_hours: float = 500.0,
    ) -> Dict[str, Any]:
        """
        Formulation 1: Financial Optimization Objective Function
        Maximize F = sum_{i} ( Q_i * Rebate_Rate * I(OEE_i >= 85%) * I(CI_i < mu_plant) )
        Subject to: sum(Q_i) >= Demand_target AND Downtime_i <= Max_Limit
        """
        rate = rebate_rate if rebate_rate is not None else self.default_rebate_rate

        if not line_metrics:
            return {
                "total_maximized_rebate_benefit": 0.0,
                "qualifying_lines_count": 0,
                "total_production_qty": 0.0,
                "constraints_met": True,
            }

        # Calculate plant average carbon intensity (\mu_{plant})
        active_cis = [
            float(m.get("co2_per_product_kg", 0.0))
            for m in line_metrics
            if float(m.get("actual_qty", 0.0)) > 0.0
        ]
        mu_plant = sum(active_cis) / len(active_cis) if active_cis else self.benchmark_ci_threshold

        total_rebate = 0.0
        qualifying_lines = 0
        total_qty = 0.0

        for line in line_metrics:
            q_i = float(line.get("actual_qty", 0.0))
            oee_i = float(line.get("oee_pct", 0.0))
            ci_i = float(line.get("co2_per_product_kg", 0.0))
            downtime_i = float(line.get("downtime_hrs", 0.0))

            total_qty += q_i

            # Indicator functions: I(OEE >= 85%) and I(CI < mu_plant) and Downtime <= Max_Limit
            i_oee = 1.0 if oee_i >= 85.0 else 0.0
            i_ci = 1.0 if (q_i > 0.0 and ci_i < mu_plant) else 0.0
            i_downtime = 1.0 if downtime_i <= max_downtime_hours else 0.0

            line_rebate = q_i * rate * i_oee * i_ci * i_downtime
            total_rebate += line_rebate

            if i_oee and i_ci and i_downtime:
                qualifying_lines += 1

        constraints_met = (total_qty >= demand_target)

        return {
            "total_maximized_rebate_benefit": round(total_rebate, 2),
            "qualifying_lines_count": qualifying_lines,
            "total_production_qty": total_qty,
            "plant_mean_carbon_intensity": round(mu_plant, 6),
            "constraints_met": constraints_met,
        }

    def evaluate_line_incentive_eligibility(
        self,
        line_code: str,
        avg_oee_pct: float,
        co2_per_product_kg: float,
        data_status: str = "ESTIMATED_PROXY",
        verification_status: str = "REQUIRES_EXTERNAL_VERIFICATION",
        plant_location: str = "UNKNOWN",
        industry: str = "Manufacturing (sub-sector inferred, see Industry_Master)",
        government_scheme_required: bool = True,
        is_metered: bool = False,
    ) -> Dict[str, Any]:
        """
        Evaluates tax incentive eligibility and generates financial screening audit payloads.
        """
        # Rule 2: Missing jurisdictional context guardrail
        if plant_location in ["UNKNOWN", "MISSING", "PENDING_CONFIRMATION"]:
            jurisdiction = "UNKNOWN - requires plant location confirmation (see Industry_Master)"
            jurisdiction_status = "REQUIRES_LOCATION_CONFIRMATION"
            block_rebate_calc = True
        else:
            jurisdiction = plant_location
            jurisdiction_status = "CONFIRMED"
            block_rebate_calc = False

        # Formulation 2: Incentive Eligibility Gate
        # Eligibility_Screen = CANDIDATE_FOR_REVIEW if (Avg_OEE_pct >= 80.0) AND (Estimated_CI <= Benchmark)
        # AND (Verification_Status == 'REQUIRES_EXTERNAL_VERIFICATION') else NOT_FLAGGED
        is_high_oee = avg_oee_pct >= 80.0
        is_low_ci = co2_per_product_kg <= self.benchmark_ci_threshold
        is_req_verif = verification_status in ["REQUIRES_EXTERNAL_VERIFICATION", "UNVERIFIED", "VERIFIED"]

        if is_high_oee and is_low_ci and is_req_verif and not block_rebate_calc:
            eligibility_screen = "CANDIDATE_FOR_REVIEW"
            tech_category = "High equipment utilization / energy-efficient operation (screen only)"
            potential_incentive_category = (
                "Energy-efficiency / low-emission-intensity operational category "
                "(generic label only -- NOT a named scheme)"
            )
        else:
            eligibility_screen = "NOT_FLAGGED"
            tech_category = "None flagged"
            potential_incentive_category = None

        investment_category = "Existing plant & machinery / operational efficiency"

        # Formulation 3: Confidence Score Assignment
        # Default 0.383 (Low for proxy data) or up to 0.85 if sub-metered and audited
        if is_metered and verification_status == "VERIFIED":
            confidence_score = 0.850
            confidence_level = "HIGH"
        else:
            confidence_score = 0.383
            confidence_level = "LOW"

        # Rule 5: If government_scheme_required is True, mark source validation and external tax review as mandatory
        if government_scheme_required:
            source_required = True
            external_tax_review_mandatory = True
        else:
            source_required = False
            external_tax_review_mandatory = False

        # Rule 4: Maintain absolute traceability linking Dashboard_KPI metrics to Tax_Incentive_Screening fields
        traceability = {
            "upstream_source": "Dashboard_KPI.csv",
            "line_code": line_code,
            "avg_oee_pct": round(avg_oee_pct, 6),
            "avg_co2_per_product_kg": round(co2_per_product_kg, 6),
            "data_status": data_status,
            "verification_status": verification_status,
            "downstream_target": "Report_Generation_Agent",
        }

        # Rule 3: Strict Parsable JSON Schema Output
        return {
            "line_code": line_code,
            "industry": industry,
            "investment_category": investment_category,
            "technology_category": tech_category,
            "potential_incentive_category": potential_incentive_category,
            "eligibility_screen": eligibility_screen,
            "government_scheme_required": bool(government_scheme_required),
            "scheme_name": None,  # Generic screening -- no hallucinated named scheme
            "jurisdiction": jurisdiction,
            "jurisdiction_status": jurisdiction_status,
            "effective_period": None,
            "source_required": source_required,
            "external_tax_review_mandatory": external_tax_review_mandatory,
            "verification_status": verification_status,
            "disclaimer": self.MANDATORY_DISCLAIMER,
            "confidence_score": confidence_score,
            "confidence_level": confidence_level,
            "avg_oee_pct": round(avg_oee_pct, 6),
            "avg_co2_per_product_kg": round(co2_per_product_kg, 6),
            "traceability": traceability,
        }

    def process_emission_and_kpi_records(
        self,
        emission_records: List[Dict[str, Any]],
        dashboard_kpis: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Ingest records from Agent 1 (or Carbon_Emission.csv / Dashboard_KPI.csv),
        compute line OEE & carbon intensity, and generate tax incentive evaluations.
        """
        if not emission_records:
            return []

        df = pd.DataFrame(emission_records)

        if "line_code" not in df.columns:
            raise ValueError("Input emission records must contain 'line_code'.")

        # Map optional Dashboard KPI lookup if provided
        kpi_map = {}
        if dashboard_kpis:
            for k in dashboard_kpis:
                l_code = str(k.get("line_code", ""))
                kpi_map[l_code] = k

        results: List[Dict[str, Any]] = []

        # Process per unique line
        for line, group in df.groupby("line_code"):
            line_str = str(line)
            # Average OEE from group or dashboard KPI
            if "oee_pct" in group.columns:
                avg_oee = float(group["oee_pct"].mean())
            elif line_str in kpi_map and "avg_oee_pct" in kpi_map[line_str]:
                avg_oee = float(kpi_map[line_str]["avg_oee_pct"])
            else:
                avg_oee = 80.0

            # Average carbon intensity per product
            if "co2_per_product_kg" in group.columns:
                active_ci = group[group["co2_per_product_kg"] > 0]["co2_per_product_kg"]
                avg_ci = float(active_ci.mean()) if not active_ci.empty else float(group["co2_per_product_kg"].mean())
            else:
                avg_ci = self.benchmark_ci_threshold

            data_status = str(group["data_status"].iloc[0]) if "data_status" in group.columns else "ESTIMATED_PROXY"
            is_metered = bool(group["is_metered"].iloc[0]) if "is_metered" in group.columns else False

            eval_res = self.evaluate_line_incentive_eligibility(
                line_code=line_str,
                avg_oee_pct=avg_oee,
                co2_per_product_kg=avg_ci,
                data_status=data_status,
                verification_status="REQUIRES_EXTERNAL_VERIFICATION",
                plant_location="UNKNOWN",
                government_scheme_required=True,
                is_metered=is_metered,
            )

            results.append(eval_res)

        return results

    def run_pipeline(
        self,
        emission_input: Union[str, List[Dict[str, Any]]],
        dashboard_kpi_input: Optional[Union[str, List[Dict[str, Any]]]] = None,
        output_json_path: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        End-to-end tax incentive optimization pipeline taking Agent 1 emission records or file path.
        """
        if isinstance(emission_input, str):
            logger.info(f"Agent 4: Ingesting emission logs from CSV file: {emission_input}")
            df = pd.read_csv(emission_input)
            records = df.to_dict(orient="records")
        else:
            logger.info(f"Agent 4: Ingesting {len(emission_input)} emission records directly from pipeline memory.")
            records = emission_input

        kpi_records = None
        if isinstance(dashboard_kpi_input, str):
            logger.info(f"Agent 4: Ingesting Dashboard KPIs from: {dashboard_kpi_input}")
            kpi_df = pd.read_csv(dashboard_kpi_input)
            kpi_records = kpi_df.to_dict(orient="records")
        elif isinstance(dashboard_kpi_input, list):
            kpi_records = dashboard_kpi_input

        results = self.process_emission_and_kpi_records(records, dashboard_kpis=kpi_records)

        if output_json_path:
            logger.info(f"Agent 4: Exporting audit-ready Tax Incentive JSON to: {output_json_path}")
            with open(output_json_path, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2)

        return results
