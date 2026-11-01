export const summary = {
  totalEmissionsKg: 86457,
  totalEmissionsTons: 86.46,
  emissionsTrendPct: -4.7,
  potentialCreditsTco2e: 4.283863,
  creditsTrendPct: 5.2,
  confidenceScore: 0.45, // 45.0% - LOW due to proxy allocation cap
  confidenceRating: "LOW (PROXY CAP <= 0.45)",
  complianceStatus: "PENDING_AUDIT" as "PASS" | "FLAGGED" | "PENDING_AUDIT",
  gridFactor: 0.716,
  totalEnergyKwh: 120750,
  evaluatedLinesCount: 26,
  linesWithReductionCount: 9,
  lastRun: "2026-08-22 (Agent Pipeline Output)",
};

export type LineRow = {
  line: string;
  product: string;
  energyKwh: number;
  co2Kg: number;
  ci: number;
  oee: number;
  lineage: "METERED" | "ESTIMATED_PROXY";
};

export const lines: LineRow[] = [
  { line: "M5L011", product: "Precision Motor Housing", energyKwh: 5400, co2Kg: 3866.4, ci: 0.386, oee: 88.5, lineage: "ESTIMATED_PROXY" },
  { line: "M5L012", product: "Alloy Engine Block", energyKwh: 5200, co2Kg: 3723.2, ci: 0.412, oee: 87.2, lineage: "ESTIMATED_PROXY" },
  { line: "M5L013", product: "HVAC Blower Casing", energyKwh: 4950, co2Kg: 3544.2, ci: 0.405, oee: 86.1, lineage: "ESTIMATED_PROXY" },
  { line: "M5L014", product: "Turbine Blade Assembly", energyKwh: 5100, co2Kg: 3651.6, ci: 0.456, oee: 84.0, lineage: "ESTIMATED_PROXY" },
  { line: "M5L015", product: "Cast Cylinder Head", energyKwh: 4800, co2Kg: 3436.8, ci: 0.394, oee: 89.0, lineage: "ESTIMATED_PROXY" },
  { line: "M5L016", product: "Rotor Stator Core", energyKwh: 4700, co2Kg: 3365.2, ci: 0.388, oee: 88.0, lineage: "ESTIMATED_PROXY" },
  { line: "M5L017", product: "Transmission Shaft", energyKwh: 4900, co2Kg: 3508.4, ci: 0.441, oee: 82.5, lineage: "ESTIMATED_PROXY" },
  { line: "M5L018", product: "Hydraulic Pump Body", energyKwh: 4600, co2Kg: 3293.6, ci: 0.379, oee: 90.1, lineage: "ESTIMATED_PROXY" },
  { line: "M5L019", product: "Flywheel Housing", energyKwh: 4850, co2Kg: 3472.6, ci: 0.432, oee: 83.4, lineage: "ESTIMATED_PROXY" },
  { line: "M5L020", product: "Electric Axle Casing", energyKwh: 4550, co2Kg: 3257.8, ci: 0.372, oee: 91.2, lineage: "ESTIMATED_PROXY" },
  { line: "M5L021", product: "Gearbox Shell", energyKwh: 4750, co2Kg: 3401.0, ci: 0.425, oee: 85.0, lineage: "ESTIMATED_PROXY" },
  { line: "M5L022", product: "Coil Assembly", energyKwh: 4500, co2Kg: 3222.0, ci: 0.368, oee: 92.0, lineage: "ESTIMATED_PROXY" },
  { line: "M5L023", product: "Control Valve Mount", energyKwh: 4820, co2Kg: 3451.1, ci: 0.435, oee: 83.1, lineage: "ESTIMATED_PROXY" },
  { line: "M5L024", product: "Piston Rod Insert", energyKwh: 4680, co2Kg: 3350.9, ci: 0.418, oee: 85.6, lineage: "ESTIMATED_PROXY" },
  { line: "M5L025", product: "Differential Case", energyKwh: 4450, co2Kg: 3186.2, ci: 0.362, oee: 93.0, lineage: "ESTIMATED_PROXY" },
  { line: "M5L026", product: "Bearing Hub Ring", energyKwh: 4720, co2Kg: 3379.5, ci: 0.428, oee: 84.8, lineage: "ESTIMATED_PROXY" },
];

export const emissionSeries = lines.map((l) => ({
  line: l.line,
  actual: Math.round(l.co2Kg),
  baseline: Math.round(l.co2Kg * 1.08),
  intensity: l.ci,
}));

export const ragChunks = [
  {
    docId: "CEA_GRID_BASELINE_2026",
    title: "CEA All-India Grid Emission Factor Baseline 2026 (POL-001)",
    body:
      "The Combined Margin (CM) grid emission factor for the All-India regional grid is established at 0.716 kg CO2/kWh for 2026 compliance. Unmetered proxy allocations must benchmark calculations against the 0.750 kg CO2/kWh regulatory limit.",
    score: 0.92,
    mandate: "VERIFIED" as const,
  },
  {
    docId: "CCTS_OFFSET_MECH_v2.1",
    title: "Carbon Credit Trading Scheme (CCTS) Registration Mandate (POL-002)",
    body:
      "Quantification of potential carbon credits (PC_i in tCO2e) requires a 7-day initial baseline, active period net reductions (Delta C_i), registry-approved methodology, additionality demonstration, and accredited MRV verification.",
    score: 0.88,
    mandate: "VERIFIED" as const,
  },
  {
    docId: "GREEN_TAX_INCENTIVE_ACT_2025",
    title: "National Green Manufacturing & Tax Incentive Act Clause 12b (POL-003)",
    body:
      "Industrial production lines maintaining OEE >= 85.0% and carbon intensity per product unit below plant average qualify for financial rebate optimization screening under green manufacturing capital allowance schemes.",
    score: 0.85,
    mandate: "PENDING_REVIEW" as const,
  },
  {
    docId: "VERRA_CDM_MRV_MANDATE_v4.4",
    title: "Verra / CDM Registry Rules Annex III (POL-004)",
    body:
      "Unmetered proxy allocated energy telemetry (40% runtime, 35% output, 25% OEE) limits composite confidence score to CS_composite <= 0.45. Third-party physical sub-metering is mandatory prior to statutory filing.",
    score: 0.81,
    mandate: "PENDING_REVIEW" as const,
  },
];

export const incentives = [
  {
    name: "Financial Rebate Objective Optimization (F = sum Q_i * Rate)",
    ref: "Tax Agent Stage 4 Optimization",
    value: "26 Lines Evaluated",
    basis: "Objective function maximized across 26 operating lines; 9 lines meeting carbon intensity reduction benchmark",
    eligible: true,
  },
  {
    name: "Green Manufacturing Capital Allowance",
    ref: "NGMTIA 2025 Clause 12b",
    value: "Screening Qualified",
    basis: "Average line OEE 87.4% exceeds 80.0% threshold requirement",
    eligible: true,
  },
  {
    name: "Accelerated Depreciation for Energy Assets",
    ref: "Sec. 32(1)(iia) Green Tax Framework",
    value: "Candidate for Review",
    basis: "Equipment efficiency and carbon intensity metrics clear initial KPI screening filters",
    eligible: true,
  },
  {
    name: "Automated Tax Rebate Calculation",
    ref: "Jurisdiction Location Guardrail (Rule 2)",
    value: "Blocked (Confirmation Needed)",
    basis: "Plant location is UNKNOWN - jurisdiction set to REQUIRES_LOCATION_CONFIRMATION to prevent unverified claims",
    eligible: false,
  },
];

export const auditNotices = [
  {
    level: "WARNING" as const,
    text: "MANDATORY AUDIT ADVISORY: Composite confidence score is LOW (CS_composite = 0.45) due to reliance on unmetered proxy energy telemetry (40% runtime, 35% output, 25% OEE). Physical sub-meters and independent MRV verification required.",
  },
  {
    level: "WARNING" as const,
    text: "Policy Compliance RAG: All 26 production lines assigned PENDING_PLANT_SUBMETER_AUDIT compliance posture under Rule 1 proxy guardrail.",
  },
  {
    level: "WARNING" as const,
    text: "Tax Incentive Optimization: Automated rebate issuance blocked (REQUIRES_LOCATION_CONFIRMATION) until plant jurisdictional location is confirmed.",
  },
  {
    level: "INFO" as const,
    text: "Report synthesized by Agent 5 (Report Generation Agent) from Agents 1-4. Plant Total CO2: 86.46 tCO2; Carbon Credit Headroom: 4.283863 tCO2e.",
  },
];

export const reportSummary = `Plant M5 (Pune Works) recorded 86,457 kg CO2e (86.46 tCO2) across 26 active manufacturing lines for reporting period 2026-07. Total allocated energy consumed across all lines reached 120,750.00 kWh using the CEA All-India Combined Margin factor of 0.716 kg CO2/kWh.

The multi-agent pipeline evaluated rolling 7-day initial operating baselines against active period emissions. Net estimated CO2 reduction across 9 qualifying lines totaled 4,283.86 kg CO2, unlocking an estimated 4.283863 tCO2e of potential carbon credit headroom under CCTS v2.1 screening.

Composite confidence score settled at 0.45 (LOW) due to the mandatory unmetered proxy data guardrail (is_metered = False). RAG policy compliance audit returned PENDING_PLANT_SUBMETER_AUDIT posture across all 26 lines. Tax incentive optimization completed candidate screening across all lines; automated financial rebate calculation remains blocked pending plant location confirmation.`;

/**
 * Dynamic loader function that fetches real output JSON files from /data/
 */
export async function fetchRealPipelineData() {
  try {
    const reportRes = await fetch("/data/executive_report_output.json");
    if (!reportRes.ok) return null;
    const reportData = await reportRes.json();

    const emissionRes = await fetch("/data/emission_assessment_output.json");
    const creditRes = await fetch("/data/carbon_credit_assessment_output.json");
    const policyRes = await fetch("/data/policy_compliance_output.json");
    const taxRes = await fetch("/data/tax_incentive_output.json");

    return {
      report: reportData,
      emissions: emissionRes.ok ? await emissionRes.json() : [],
      credits: creditRes.ok ? await creditRes.json() : [],
      policies: policyRes.ok ? await policyRes.json() : [],
      taxes: taxRes.ok ? await taxRes.json() : [],
    };
  } catch (err) {
    console.warn("Failed to fetch real pipeline data from /data/, using default metrics.", err);
    return null;
  }
}
