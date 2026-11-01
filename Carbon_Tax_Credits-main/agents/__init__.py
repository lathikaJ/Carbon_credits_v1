"""
Agents Package
==============
Industrial AI Autonomous Agents for Carbon Emissions, Credit Assessment, Policy RAG Compliance, Tax Incentive Optimization, and Executive Report Generation.
"""

from .policy_compliance_agent import PolicyComplianceAgent

try:
    from .emission_assessment_agent import EmissionAssessmentAgent
    from .carbon_credit_assessment_agent import CarbonCreditAssessmentAgent
    from .tax_incentive_agent import TaxIncentiveAgent
    from .report_generation_agent import ReportGenerationAgent
    from .pipeline import AgentPipeline
except ImportError:
    EmissionAssessmentAgent = None  # type: ignore
    CarbonCreditAssessmentAgent = None  # type: ignore
    TaxIncentiveAgent = None  # type: ignore
    ReportGenerationAgent = None  # type: ignore
    AgentPipeline = None  # type: ignore

__all__ = [
    "EmissionAssessmentAgent",
    "CarbonCreditAssessmentAgent",
    "PolicyComplianceAgent",
    "TaxIncentiveAgent",
    "ReportGenerationAgent",
    "AgentPipeline",
]
