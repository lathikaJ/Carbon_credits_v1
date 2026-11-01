"""
Emission Assessment Agent (Agent 1)
====================================
An autonomous, deterministic industrial AI component responsible for calculating
greenhouse gas (GHG) and carbon emissions from raw, unmetered, and messy manufacturing telemetry.

Mathematical Formulations Executed:
1. Weighted Allocation Share (W_{i,t}):
   W_{i,t} = 0.40 * (h_{i,t} / H_{total,t}) + 0.35 * (Q_{i,t} / sum(Q_{i,t})) + 0.25 * (OEE_{i,t} / sum(OEE_{i,t}))
2. Allocated Energy (E_{i,t} in kWh):
   E_{i,t} = P_{plant,t} * W_{i,t}
3. Estimated Carbon Emission (C_{i,t} in kg CO2):
   C_{i,t} = E_{i,t} * EF_{grid}  (EF_{grid} = 0.716 kg CO2/kWh)
4. Carbon Intensity per Product (CI_{i,t}):
   CI_{i,t} = C_{i,t} / Q_{i,t}  (If Q_{i,t} == 0 -> CI_{i,t} = 0, status = 'PLANNED_SHUTDOWN')
5. Normalized Carbon Score (CS_{i,t}):
   CS_{i,t} = 100 * (1 - ((CI_{i,t} - min(CI_{batch})) / (max(CI_{batch}) - min(CI_{batch}))))

Execution Rules & Guardrails:
- Rule 1: If is_metered is False, cap maximum confidence score strictly at 0.45 and set data_status to 'ESTIMATED_PROXY'.
- Rule 2: Prevent ZeroDivisionError across all operations; default to 0 if denominator is 0.
- Rule 3: Output all results in a strict, parsable JSON schema.
- Rule 4: Mark blank/missing variables as 'NOT_AVAILABLE' and flag for external audit.
- Rule 5: Maintain strict end-to-end traceability between raw telemetry rows and final calculated outputs.
"""

import math
import json
import logging
from typing import Dict, List, Any, Union, Optional
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("EmissionAssessmentAgent")


class EmissionAssessmentAgent:
    """
    Agent 1: Autonomous, deterministic industrial AI component for GHG emission calculation
    and proxy allocation from raw plant telemetry.
    """

    DEFAULT_GRID_EF: float = 0.716  # CEA All-India Weighted Average baseline (kg CO2/kWh)
    CONFIDENCE_CAP_UNMETERED: float = 0.45
    CONFIDENCE_DIRECT_METERED: float = 0.95

    FORMULA_SHARE_STR: str = "0.40*(runtime_hours/H_total) + 0.35*(actual_qty/sum_qty) + 0.25*(oee/sum_oee)"
    FORMULA_ENERGY_STR: str = "allocated_energy_kwh = plant_machine_power_source_value * allocation_weight"
    FORMULA_CO2_STR: str = "estimated_co2_kg = allocated_energy_kwh * grid_emission_factor_kgco2_per_kwh"
    FORMULA_CI_STR: str = "co2_per_product_kg = estimated_co2_kg / actual_qty"
    FORMULA_CS_STR: str = "carbon_score = 100 * (1 - ((CI - min(CI_batch)) / (max(CI_batch) - min(CI_batch))))"

    ASSUMPTION_TEXT: str = (
        "Only plant-level 'Machine Power' (kWh/day) is metered. Daily plant Machine Power is allocated "
        "across production lines using a weighted operational proxy (40% runtime, 35% output, 25% OEE). "
        "Grid emission factor baseline = 0.716 kgCO2/kWh (CEA All-India OM Average)."
    )

    def __init__(
        self,
        grid_emission_factor: float = DEFAULT_GRID_EF,
        confidence_cap_unmetered: float = CONFIDENCE_CAP_UNMETERED,
    ):
        self.grid_emission_factor = float(grid_emission_factor)
        self.confidence_cap_unmetered = float(confidence_cap_unmetered)

    def render_prompt(self, context: Dict[str, Any], prompt_path: str = "prompts/emission_agent.j2") -> str:
        """Renders the Agent 1 Jinja prompt template with runtime variables."""
        import os
        import jinja2
        if os.path.exists(prompt_path):
            with open(prompt_path, "r", encoding="utf-8") as f:
                template = jinja2.Template(f.read())
            return template.render(**context)
        return ""

    @staticmethod
    def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
        """Rule 2: Cross-check all division operations to prevent ZeroDivisionError."""
        try:
            if denominator is None or math.isnan(denominator) or denominator == 0:
                return default
            if numerator is None or math.isnan(numerator):
                return default
            return float(numerator / denominator)
        except ZeroDivisionError:
            return default

    def calculate_weighted_allocation(
        self,
        runtime_hours: float,
        h_total: float,
        actual_qty: float,
        sum_qty: float,
        oee_pct: float,
        sum_oee: float,
    ) -> Dict[str, float]:
        """
        Executes Formulation 1:
        W_{i,t} = 0.40 * (h_{i,t} / H_{total,t}) + 0.35 * (Q_{i,t} / sum(Q_{i,t})) + 0.25 * (OEE_{i,t} / sum(OEE_{i,t}))
        """
        runtime_share = self.safe_divide(runtime_hours, h_total)
        qty_share = self.safe_divide(actual_qty, sum_qty)
        oee_share = self.safe_divide(oee_pct, sum_oee)

        allocation_weight = 0.40 * runtime_share + 0.35 * qty_share + 0.25 * oee_share

        return {
            "runtime_share": runtime_share,
            "qty_share": qty_share,
            "oee_share": oee_share,
            "allocation_weight": allocation_weight,
        }

    def process_telemetry_batch(
        self,
        telemetry_records: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Ingest raw telemetry records and process calculations deterministically by date batch.
        Each record can contain production metrics and energy telemetry.
        """
        if not telemetry_records:
            return []

        # Convert to DataFrame for batch processing and date grouping
        df = pd.DataFrame(telemetry_records)

        # Validate mandatory grouping keys
        if "date" not in df.columns or "line_code" not in df.columns:
            raise ValueError("Input records must contain 'date' and 'line_code' fields.")

        results: List[Dict[str, Any]] = []

        # Process date by date
        for date_val, group in df.groupby("date"):
            # Batch totals for allocation shares (Rule 2: Safe summation)
            h_total = group["runtime_hours"].fillna(0.0).astype(float).sum()
            sum_qty = group["actual_qty"].fillna(0.0).astype(float).sum()

            # Handle OEE field variations (oee_pct_clean, oee_pct_raw, or oee_pct)
            oee_col = "oee_pct_clean" if "oee_pct_clean" in group.columns else (
                "oee_pct_raw" if "oee_pct_raw" in group.columns else "oee_pct"
            )
            sum_oee = group[oee_col].fillna(0.0).astype(float).sum() if oee_col in group.columns else 0.0

            # Step 1: Compute allocation, energy, and raw CO2 for all lines in the date batch
            batch_intermediate = []

            for idx, row in group.iterrows():
                line_code = str(row["line_code"])

                # Extract telemetry fields with strict Rule 4 check
                runtime_h = row.get("runtime_hours")
                qty = row.get("actual_qty")
                oee_val = row.get(oee_col, 0.0) if oee_col in row else 0.0
                plant_power = row.get("plant_machine_power_source_value")

                # Metered status check (Rule 1)
                is_metered_raw = row.get("is_metered", False)
                is_metered = bool(is_metered_raw) if pd.notna(is_metered_raw) else False

                # Rule 4: Check if essential source fields are missing/blank
                missing_fields = []
                if pd.isna(runtime_h):
                    missing_fields.append("runtime_hours")
                if pd.isna(qty):
                    missing_fields.append("actual_qty")
                if pd.isna(plant_power):
                    missing_fields.append("plant_machine_power_source_value")

                field_status = "NOT_AVAILABLE" if missing_fields else "OBSERVED"
                requires_audit = len(missing_fields) > 0

                # Sanitize numeric values (Rule 2)
                runtime_h_val = float(runtime_h) if pd.notna(runtime_h) else 0.0
                qty_val = float(qty) if pd.notna(qty) else 0.0
                oee_val_clean = float(oee_val) if pd.notna(oee_val) else 0.0
                plant_power_val = float(plant_power) if pd.notna(plant_power) else 0.0

                # 1. Weighted Allocation Share
                alloc_res = self.calculate_weighted_allocation(
                    runtime_hours=runtime_h_val,
                    h_total=h_total,
                    actual_qty=qty_val,
                    sum_qty=sum_qty,
                    oee_pct=oee_val_clean,
                    sum_oee=sum_oee,
                )
                allocation_weight = alloc_res["allocation_weight"]

                # 2. Allocated Energy
                # If direct line energy is already metered, use it; else proxy allocate
                if is_metered and pd.notna(row.get("line_metered_energy_kwh")):
                    allocated_energy_kwh = float(row["line_metered_energy_kwh"])
                else:
                    allocated_energy_kwh = plant_power_val * allocation_weight

                # 3. Estimated Carbon Emission
                estimated_co2_kg = allocated_energy_kwh * self.grid_emission_factor

                # 4. Carbon Intensity per Product
                if qty_val == 0.0:
                    co2_per_product_kg = 0.0
                    production_status = "PLANNED_SHUTDOWN"
                else:
                    co2_per_product_kg = self.safe_divide(estimated_co2_kg, qty_val)
                    production_status = str(row.get("production_status", "PRODUCTION"))
                    if production_status not in ["PRODUCTION", "PLANNED_SHUTDOWN"]:
                        production_status = "PRODUCTION"

                batch_intermediate.append({
                    "line_code": line_code,
                    "date": str(date_val),
                    "runtime_hours": runtime_h_val,
                    "actual_qty": qty_val,
                    "oee_pct": oee_val_clean,
                    "plant_machine_power_source_value": plant_power_val,
                    "runtime_share": alloc_res["runtime_share"],
                    "qty_share": alloc_res["qty_share"],
                    "oee_share": alloc_res["oee_share"],
                    "allocation_weight": allocation_weight,
                    "allocated_energy_kwh": allocated_energy_kwh,
                    "estimated_co2_kg": estimated_co2_kg,
                    "co2_per_product_kg": co2_per_product_kg,
                    "is_metered": is_metered,
                    "production_status": production_status,
                    "field_status": field_status,
                    "requires_audit": requires_audit,
                    "missing_fields": missing_fields,
                    "source_file": str(row.get("source_file", "telemetry_input")),
                    "source_row": row.get("source_row", None),
                })

            # Step 2: Compute relative Carbon Score CS_{i,t} across active lines in the date batch (Formulation 5)
            active_ci = [
                item["co2_per_product_kg"]
                for item in batch_intermediate
                if item["actual_qty"] > 0.0
            ]

            min_ci = min(active_ci) if active_ci else 0.0
            max_ci = max(active_ci) if active_ci else 0.0
            ci_range = max_ci - min_ci

            # Step 3: Format final structured, audit-ready output items
            for item in batch_intermediate:
                # Rule 1: Guardrail for confidence score and data_status
                if not item["is_metered"]:
                    confidence_score = min(0.45, self.confidence_cap_unmetered)
                    data_status = "ESTIMATED_PROXY"
                    confidence_level = "LOW"
                else:
                    confidence_score = self.CONFIDENCE_DIRECT_METERED
                    data_status = "DIRECT_METERED"
                    confidence_level = "HIGH"

                # Formulation 5: Carbon Score calculation
                if item["actual_qty"] == 0.0:
                    carbon_score = 0.0
                elif ci_range == 0.0:
                    carbon_score = 100.0
                else:
                    normalized = self.safe_divide(item["co2_per_product_kg"] - min_ci, ci_range)
                    carbon_score = 100.0 * (1.0 - normalized)

                # Combined calculation formula string (Rule 3)
                formula_trail = (
                    f"W = 0.40*({item['runtime_hours']:.2f}/{h_total:.2f}) + "
                    f"0.35*({item['actual_qty']:.0f}/{sum_qty:.0f}) + "
                    f"0.25*({item['oee_pct']:.2f}/{sum_oee:.2f}) = {item['allocation_weight']:.6f}; "
                    f"E = {item['plant_machine_power_source_value']:.2f} * {item['allocation_weight']:.6f} = {item['allocated_energy_kwh']:.4f} kWh; "
                    f"C = {item['allocated_energy_kwh']:.4f} * {self.grid_emission_factor} = {item['estimated_co2_kg']:.4f} kg CO2; "
                    f"CI = {item['estimated_co2_kg']:.4f} / {item['actual_qty']:.0f} = {item['co2_per_product_kg']:.6f} kg/unit; "
                    f"CS = 100 * (1 - ({item['co2_per_product_kg']:.6f} - {min_ci:.6f})/({ci_range:.6f})) = {carbon_score:.2f}"
                )

                audit_record = {
                    "line_code": item["line_code"],
                    "date": item["date"],
                    "allocated_energy_kwh": round(item["allocated_energy_kwh"], 6),
                    "estimated_co2_kg": round(item["estimated_co2_kg"], 6),
                    "co2_per_product_kg": round(item["co2_per_product_kg"], 6),
                    "carbon_score": round(carbon_score, 4),
                    "confidence_score": confidence_score,
                    "confidence_level": confidence_level,
                    "data_status": data_status,
                    "production_status": item["production_status"],
                    "field_status": item["field_status"],
                    "flagged_for_audit": item["requires_audit"],
                    "is_metered": item["is_metered"],
                    "grid_emission_factor_kgco2_per_kwh": self.grid_emission_factor,
                    "calculation_formula": self.FORMULA_CO2_STR,
                    "formula_used": formula_trail,
                    "assumption": self.ASSUMPTION_TEXT,
                    "traceability": {
                        "runtime_share": round(item["runtime_share"], 8),
                        "qty_share": round(item["qty_share"], 8),
                        "oee_share": round(item["oee_share"], 8),
                        "allocation_weight": round(item["allocation_weight"], 8),
                        "source_file": item["source_file"],
                        "source_row": item["source_row"],
                        "missing_fields": item["missing_fields"],
                    },
                }

                results.append(audit_record)

        return results

    def run_pipeline(
        self,
        production_csv_path: str,
        energy_proxy_csv_path: str,
        output_json_path: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        End-to-end ingestion and emission calculation pipeline for manufacturing datasets.
        """
        logger.info(f"Agent 1: Ingesting production telemetry from: {production_csv_path}")
        prod_df = pd.read_csv(production_csv_path)

        logger.info(f"Agent 1: Ingesting energy proxy telemetry from: {energy_proxy_csv_path}")
        energy_df = pd.read_csv(energy_proxy_csv_path)

        # Merge production and energy data on line_code and date
        merged = pd.merge(
            prod_df,
            energy_df,
            on=["line_code", "date"],
            how="outer",
            suffixes=("_prod", "_energy"),
        )

        records = merged.to_dict(orient="records")

        logger.info(f"Agent 1: Processing {len(records)} line-day telemetry records...")
        results = self.process_telemetry_batch(records)

        if output_json_path:
            logger.info(f"Agent 1: Exporting structured emission JSON logs to: {output_json_path}")
            with open(output_json_path, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2)

        return results
