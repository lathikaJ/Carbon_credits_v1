"""
Carbon Credit Assessment Agent (Agent 2)
=========================================
An autonomous, deterministic industrial AI component responsible for evaluating
carbon reduction potentials, screening eligibility, and quantifying potential carbon
credit units from factory emission logs (output of Agent 1 / Carbon_Emission.csv).

Mathematical Formulations Executed:
1. Baseline Emission Calculation (\bar{C}_{i,base}):
   \bar{C}_{i,base} = (1 / 7) * sum(C_{i,\tau}) for \tau in first 7 observed operating days of line i.

2. Estimated Emission Reduction (\Delta C_i):
   \Delta C_i = max(0, \bar{C}_{i,base} - \bar{C}_{i,current}) * D_{observed}
   Where D_{observed} = total active observation days in the assessment period.

3. Potential Credit Quantity (PC_i in tCO2e):
   PC_i = \Delta C_i / 1000
   Subject to strict compliance gate:
   Eligible = Methodology_Required AND Additionality_Required AND Verification_Required.

4. Confidence Score Assignment:
   If screening-only status is active without independent third-party MRV, confidence_level
   must be set strictly to 'VERY_LOW' (score <= 0.20, default: 0.191).

Execution Rules & Guardrails:
- Rule 1: All outputs carry disclaimer: "ILLUSTRATIVE ONLY. Actual credit issuance requires a registry-approved methodology and independent MRV verification."
- Rule 2: Guard against negative reduction values; if current emissions exceed baseline, reduction and potential credits default to 0.0.
- Rule 3: Output all results in strict JSON schema containing 'assessment_id', 'line_code', 'baseline_emission', 'estimated_current_emission', 'estimated_reduction', 'potential_credit_quantity', 'eligibility_status', 'confidence_score', and 'disclaimer'.
- Rule 4: Maintain absolute traceability back to source files such as Carbon_Emission.csv and Dashboard_KPI.csv.
- Rule 5: Missing or undefined boolean flags default status to 'REQUIRES_METHODOLOGY' and block automated issuance.
"""

import math
import json
import logging
from typing import Dict, List, Any, Optional, Union
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("CarbonCreditAssessmentAgent")


class CarbonCreditAssessmentAgent:
    """
    Agent 2: Autonomous, deterministic industrial AI component for carbon credit assessment
    and eligibility screening from emission logs.
    """

    MANDATORY_DISCLAIMER: str = (
        "ILLUSTRATIVE ONLY. Actual credit issuance requires a registry-approved methodology "
        "and independent MRV verification."
    )

    DEFAULT_CALCULATION_NOTE: str = (
        "baseline_emission = mean(Estimated_CO2_kg) over the line's first 7 observed days; "
        "estimated_reduction = max(0, baseline_emission - estimated_current_emission) * days_observed; "
        "potential_credit_quantity (tCO2e) = estimated_reduction / 1000"
    )

    DEFAULT_ASSUMPTION: str = (
        "1 tCO2e of estimated reduction is treated as approximately 1 potential carbon credit unit ONLY "
        "as a simplified analytical assumption for screening purposes. This is NOT a registry conversion rule "
        "and carries no certification value."
    )

    SCREENING_CONFIDENCE_SCORE: float = 0.191
    SCREENING_CONFIDENCE_LEVEL: str = "VERY_LOW"

    def __init__(
        self,
        confidence_score_screening: float = SCREENING_CONFIDENCE_SCORE,
    ):
        self.confidence_score_screening = float(confidence_score_screening)

    def render_prompt(self, context: Dict[str, Any], prompt_path: str = "prompts/credit_agent.j2") -> str:
        """Renders the Agent 2 Jinja prompt template with runtime variables."""
        import os
        import jinja2
        if os.path.exists(prompt_path):
            with open(prompt_path, "r", encoding="utf-8") as f:
                template = jinja2.Template(f.read())
            return template.render(**context)
        return ""

    @staticmethod
    def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
        """Rule 2: ZeroDivisionError prevention helper."""
        try:
            if denominator is None or math.isnan(denominator) or denominator == 0:
                return default
            if numerator is None or math.isnan(numerator):
                return default
            return float(numerator / denominator)
        except ZeroDivisionError:
            return default

    def calculate_line_baseline(
        self,
        emission_records: List[Dict[str, Any]],
    ) -> float:
        """
        Formulation 1: Compute baseline emission average (\bar{C}_{i,base})
        from first 7 observed operating days of line i.
        """
        if not emission_records:
            return 0.0

        # Sort chronologically by date
        sorted_records = sorted(emission_records, key=lambda x: str(x.get("date", "")))

        # Take first 7 observed operating days
        first_7 = sorted_records[:7]
        if not first_7:
            return 0.0

        total_co2 = sum(float(r.get("estimated_co2_kg", 0.0)) for r in first_7)
        return float(total_co2 / len(first_7))

    def evaluate_line_credit_eligibility(
        self,
        line_code: str,
        emission_records: List[Dict[str, Any]],
        assessment_id: Optional[str] = None,
        period_month: str = "2026-07",
        methodology_required: Optional[bool] = True,
        additionality_required: Optional[bool] = True,
        verification_required: Optional[bool] = True,
        registry_required: Optional[bool] = True,
        source_file: str = "Carbon_Emission.csv",
    ) -> Dict[str, Any]:
        """
        Evaluates carbon credit eligibility and reduction potential for a single production line.
        """
        if not emission_records:
            return {
                "assessment_id": assessment_id or f"CCA-0000",
                "line_code": line_code,
                "period_month": period_month,
                "baseline_emission": 0.0,
                "estimated_current_emission": 0.0,
                "estimated_reduction": 0.0,
                "reduction_potential": 0.0,
                "potential_credit_quantity": 0.0,
                "eligibility_screen": "SCREENING_ONLY",
                "eligibility_status": "INSUFFICIENT_DATA",
                "methodology_required": bool(methodology_required) if methodology_required is not None else False,
                "additionality_required": bool(additionality_required) if additionality_required is not None else False,
                "verification_required": bool(verification_required) if verification_required is not None else False,
                "registry_required": bool(registry_required) if registry_required is not None else False,
                "calculation_note": self.DEFAULT_CALCULATION_NOTE,
                "formula_used": self.DEFAULT_CALCULATION_NOTE,
                "assumption": self.DEFAULT_ASSUMPTION,
                "disclaimer": self.MANDATORY_DISCLAIMER,
                "confidence_score": self.confidence_score_screening,
                "confidence_level": self.SCREENING_CONFIDENCE_LEVEL,
                "traceability": {
                    "source_file": source_file,
                    "days_observed": 0,
                    "reason": "No emission records provided for line",
                },
            }

        # Formulation 1: Baseline Emission Calculation (\bar{C}_{i,base})
        baseline_emission = self.calculate_line_baseline(emission_records)

        # Active observation days (D_observed) and current daily average (\bar{C}_{i,current})
        d_observed = len(emission_records)
        total_current_co2 = sum(float(r.get("estimated_co2_kg", 0.0)) for r in emission_records)
        estimated_current_emission = float(total_current_co2 / d_observed) if d_observed > 0 else 0.0

        # Formulation 2 & Rule 2: Estimated Emission Reduction (\Delta C_i)
        # Guard against negative reduction: if current emissions exceed baseline, default to 0.0
        daily_diff = baseline_emission - estimated_current_emission
        if daily_diff > 0.0:
            estimated_reduction = daily_diff * d_observed
        else:
            estimated_reduction = 0.0

        # Formulation 3: Potential Credit Quantity (PC_i in tCO2e)
        potential_credit_quantity = estimated_reduction / 1000.0

        # Compliance Gate Verification (Rule 5: check boolean flags)
        # Default status to 'REQUIRES_METHODOLOGY' if flags are missing or undefined
        has_meth = methodology_required is True
        has_add = additionality_required is True
        has_verif = verification_required is True

        # Compliance gate boolean
        eligible_compliance_gate = has_meth and has_add and has_verif

        # Determine Eligibility Status
        # Status MUST be one of 'POTENTIAL', 'REQUIRES_METHODOLOGY', 'INSUFFICIENT_DATA', 'SCREENING_ONLY'
        if not eligible_compliance_gate or not (methodology_required and additionality_required and verification_required):
            eligibility_status = "REQUIRES_METHODOLOGY"
            # Block automated issuance if compliance gate fails
            potential_credit_quantity = 0.0 if not eligible_compliance_gate else potential_credit_quantity
        elif estimated_reduction > 0.0:
            eligibility_status = "POTENTIAL"
        else:
            eligibility_status = "REQUIRES_METHODOLOGY"

        # Formulation 4: Confidence Score Assignment
        # Screening-only status without independent 3rd party MRV -> VERY_LOW confidence (score <= 0.20)
        confidence_score = min(0.20, self.confidence_score_screening)
        confidence_level = "VERY_LOW"

        # Formula trail string
        formula_used = (
            f"baseline_emission = mean(first 7 days CO2) = {baseline_emission:.4f} kg; "
            f"current_emission = mean({d_observed} days CO2) = {estimated_current_emission:.4f} kg; "
            f"estimated_reduction = max(0, {baseline_emission:.4f} - {estimated_current_emission:.4f}) * {d_observed} = {estimated_reduction:.4f} kg; "
            f"potential_credit_quantity = {estimated_reduction:.4f} / 1000 = {potential_credit_quantity:.6f} tCO2e"
        )

        return {
            "assessment_id": assessment_id or f"CCA-{line_code}",
            "line_code": line_code,
            "period_month": period_month,
            "baseline_emission": round(baseline_emission, 6),
            "estimated_current_emission": round(estimated_current_emission, 6),
            "estimated_reduction": round(estimated_reduction, 6),
            "reduction_potential": round(estimated_reduction, 6),
            "potential_credit_quantity": round(potential_credit_quantity, 6),
            "eligibility_screen": "SCREENING_ONLY",
            "eligibility_status": eligibility_status,
            "methodology_required": bool(methodology_required) if methodology_required is not None else False,
            "additionality_required": bool(additionality_required) if additionality_required is not None else False,
            "verification_required": bool(verification_required) if verification_required is not None else False,
            "registry_required": bool(registry_required) if registry_required is not None else False,
            "calculation_note": self.DEFAULT_CALCULATION_NOTE,
            "formula_used": formula_used,
            "assumption": self.DEFAULT_ASSUMPTION,
            "disclaimer": self.MANDATORY_DISCLAIMER,
            "confidence_score": confidence_score,
            "confidence_level": confidence_level,
            "traceability": {
                "source_file": source_file,
                "days_observed": d_observed,
                "baseline_days": min(7, d_observed),
            },
        }

    def process_emission_records(
        self,
        emission_records: List[Dict[str, Any]],
        period_month: str = "2026-07",
        config_flags: Optional[Dict[str, Dict[str, bool]]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Ingest clean daily emission records from Agent 1 (or Carbon_Emission.csv),
        group by production line, and compute carbon credit assessments.
        """
        if not emission_records:
            return []

        df = pd.DataFrame(emission_records)

        if "line_code" not in df.columns or "estimated_co2_kg" not in df.columns:
            raise ValueError("Input emission records must contain 'line_code' and 'estimated_co2_kg'.")

        results: List[Dict[str, Any]] = []

        # Sort line codes deterministically
        line_codes = sorted(df["line_code"].unique())

        for idx, line in enumerate(line_codes, start=1):
            assessment_id = f"CCA-{idx:04d}"
            line_recs = df[df["line_code"] == line].to_dict(orient="records")

            # Extract config flags if provided, else default to True
            flags = (config_flags.get(line, {}) if config_flags else {})
            meth_req = flags.get("methodology_required", True)
            add_req = flags.get("additionality_required", True)
            verif_req = flags.get("verification_required", True)
            reg_req = flags.get("registry_required", True)

            assessment = self.evaluate_line_credit_eligibility(
                line_code=line,
                emission_records=line_recs,
                assessment_id=assessment_id,
                period_month=period_month,
                methodology_required=meth_req,
                additionality_required=add_req,
                verification_required=verif_req,
                registry_required=reg_req,
                source_file="Agent_1_Emission_Output",
            )

            results.append(assessment)

        return results

    def run_pipeline(
        self,
        emission_input: Union[str, List[Dict[str, Any]]],
        output_json_path: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        End-to-end carbon credit assessment pipeline taking Agent 1 emission records or file path.
        """
        if isinstance(emission_input, str):
            logger.info(f"Agent 2: Ingesting Agent 1 emission logs from CSV file: {emission_input}")
            emission_df = pd.read_csv(emission_input)
            records = emission_df.to_dict(orient="records")
        else:
            logger.info(f"Agent 2: Ingesting {len(emission_input)} Agent 1 emission records directly from pipeline memory.")
            records = emission_input

        results = self.process_emission_records(records)

        if output_json_path:
            logger.info(f"Agent 2: Exporting audit-ready Carbon Credit Assessment JSON to: {output_json_path}")
            with open(output_json_path, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2)

        return results
