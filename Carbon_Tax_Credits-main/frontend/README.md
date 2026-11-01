# EcoPulse Executive

Build a professional, modern, executive-grade React dashboard for an Industrial Decarbonization & Carbon Credit Intelligence Platform ("EcoPulse AI"). The UI should be sleek, enterprise-ready, utilizing Tailwind CSS, Lucide React icons, and Recharts for data visualization. 

The dashboard must display data from a multi-agent industrial AI pipeline across 5 key sections:

1. EXECUTIVE SUMMARY (Top Header Cards):

   - Total Plant Carbon Emissions (e.g., 14,250 kg CO2) with trend indicator.

   - Total Potential Carbon Credits (e.g., 42.5 tCO2e) available for monetization.

   - Composite Confidence Score (e.g., 88.5%) showing data reliability.

   - Plant Compliance Status Badge ("PASS" in green or "FLAGGED" in amber).

2. LINE-BY-LINE TELEMETRY & EMISSIONS (Data Table & Charts):

   - A detailed table showing manufacturing lines (e.g., M5L011A, M5L011B), allocated energy (kWh), estimated CO2 (kg), Carbon Intensity per Product (CI), and Data Lineage Status ("METERED" vs "ESTIMATED_PROXY").

   - A bar/line chart visualizing carbon emissions vs. historical baselines across active lines.

3. POLICY & COMPLIANCE RAG INSPECTOR:

   - A dedicated card or modal displaying retrieved legal chunks from the Carbon Policies Knowledge Base (e.g., "[DOC_ID: CEA_GRID_BASELINE_2026] - CEA All-India Combined Margin Baseline: 0.716 kg CO2/kWh").

   - Cosine similarity match score (e.g., 0.92) and verification mandate status.

4. GREEN TAX INCENTIVE & REBATE OPTIMIZATION:

   - Financial optimization panel showing eligible green tax rebates and capital allowances based on OEE efficiency (>=85%) and low carbon intensity.

   - Clear, mandatory disclaimer banner: "ILLUSTRATIVE SCREENING ONLY -- NOT TAX ADVICE. Flags are based purely on operational KPI thresholds."

5. AUDIT & EXECUTIVE REPORT GENERATION:

   - Summary view of synthesized report output from the Report Generation Agent.

   - Download/Export report button and audit warning notices for proxy data deficits.

Design Style: Clean corporate dark/light aesthetic, high-contrast badges for compliance status, smooth card layouts, and responsive grid design.

This project was built with [Lovable](https://lovable.dev).

## Build with Lovable

Continue developing this project in the [Lovable editor](https://lovable.dev/projects/fbd64c71-475f-4245-ada3-fe1549deb0b7).

- **Ship faster**: describe what you want to build and Lovable handles the code.
- **Stay in sync**: every change made in Lovable is committed straight to this repository.
- **Full ownership**: this code is yours. Push to `main` on GitHub and your changes sync back into Lovable, ready for your next prompt.

## Development

Prefer working locally? You need Node.js and npm — [install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating).

```sh
git clone <this-repository-url>
cd <repository-name>
npm i
npm run dev
```
