from __future__ import annotations

import os

from aidwise.models import CalculationResult, RetrievedPassage, ScenarioComparison


class GroundedExplainer:
    def __init__(self, model: str | None = None):
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-5-mini")
        self.api_key = os.getenv("OPENAI_API_KEY")

    def generate(
        self,
        query: str,
        route: str,
        evidence: list[RetrievedPassage],
        calculation: CalculationResult | None = None,
        comparison: ScenarioComparison | None = None,
    ) -> str:
        if not self.api_key:
            return self._fallback(query, route, evidence, calculation, comparison)

        try:
            from openai import OpenAI
        except ImportError:
            return self._fallback(query, route, evidence, calculation, comparison)

        evidence_block = "\n\n".join(
            f"Source: {item.source}\nExcerpt: {item.text}" for item in evidence
        )
        calc_block = ""
        if calculation:
            calc_block = (
                f"SAI: {calculation.sai}\n"
                f"Minimum Pell eligible: {calculation.minimum_pell_eligible}\n"
                f"Maximum Pell eligible: {calculation.maximum_pell_eligible}\n"
                f"Formula type: {calculation.formula_type or 'Unknown'}\n"
                f"Assets required: {calculation.assets_required}\n"
                f"Methodology: {calculation.methodology}\n"
                f"Warning: {calculation.warning or 'None'}\n"
            )
        comparison_block = comparison.summary if comparison else ""

        client = OpenAI(api_key=self.api_key)
        response = client.responses.create(
            model=self.model,
            input=[
                {
                    "role": "system",
                    "content": (
                        "You are AidWise, a financial aid assistant. "
                        "Answer only from the supplied evidence and calculation results. "
                        "If the evidence is incomplete, say so plainly. "
                        "Do not claim that the estimate is official or final."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Route: {route}\n"
                        f"User query: {query}\n\n"
                        f"Calculation context:\n{calc_block or 'None'}\n"
                        f"Scenario comparison:\n{comparison_block or 'None'}\n\n"
                        f"Evidence:\n{evidence_block or 'No evidence loaded.'}\n\n"
                        "Write a concise explanation in plain language. Mention whether the "
                        "result came from the workbook-backed calculator or a fallback path."
                    ),
                },
            ],
        )
        return response.output_text.strip() or self._fallback(
            query, route, evidence, calculation, comparison
        )

    @staticmethod
    def _fallback(
        query: str,
        route: str,
        evidence: list[RetrievedPassage],
        calculation: CalculationResult | None,
        comparison: ScenarioComparison | None,
    ) -> str:
        sentences: list[str] = [f"Route selected: {route.replace('_', ' ')}."]
        if calculation:
            basis = "workbook-backed" if "Workbook-backed" in calculation.methodology else "fallback"
            sentences.append(f"The {basis} calculator estimated an SAI of {calculation.sai}.")
            if calculation.maximum_pell_eligible:
                sentences.append("This scenario appears eligible for maximum Pell.")
            elif calculation.minimum_pell_eligible:
                sentences.append("This scenario appears eligible for minimum Pell.")
            else:
                sentences.append("This scenario does not appear Pell-eligible.")
            if calculation.formula_type:
                sentences.append(f"The workbook selected {calculation.formula_type}.")
            if calculation.warning:
                sentences.append(calculation.warning)
        if comparison:
            sentences.append(comparison.summary)
        if evidence:
            sentences.append(f"Top supporting source: {evidence[0].source}.")
        else:
            sentences.append(
                "No policy document is loaded yet, so the answer is based only on the calculator output and disclaimers."
            )
        return " ".join(sentences)
