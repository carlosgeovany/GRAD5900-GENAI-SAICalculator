from __future__ import annotations

from aidwise.calculator import WorkbookAidCalculator
from aidwise.llm import GroundedExplainer
from aidwise.models import AidInput, QueryResponse, ScenarioComparison
from aidwise.retrieval import SimpleRetriever
from aidwise.routing import classify_query


class AidWiseOrchestrator:
    def __init__(
        self,
        retriever: SimpleRetriever | None = None,
        calculator: WorkbookAidCalculator | None = None,
        explainer: GroundedExplainer | None = None,
    ):
        self.retriever = retriever or SimpleRetriever()
        self.calculator = calculator or WorkbookAidCalculator()
        self.explainer = explainer or GroundedExplainer()

    def estimate(self, aid_input: AidInput) -> QueryResponse:
        calculation = self.calculator.calculate(aid_input)
        evidence = self.retriever.search("student aid index pell eligibility")
        answer = self.explainer.generate(
            query="Explain this aid estimate.",
            route="calculation",
            evidence=evidence,
            calculation=calculation,
        )
        return QueryResponse(
            route="calculation",
            answer=answer,
            evidence=evidence,
            calculation=calculation,
        )

    def compare_income_change(self, aid_input: AidInput, income_delta: float) -> QueryResponse:
        comparison = self.calculator.compare_income_change(aid_input, income_delta)
        evidence = self.retriever.search("student aid index pell eligibility income")
        answer = self.explainer.generate(
            query=f"What happens if income changes by {income_delta}?",
            route="what_if",
            evidence=evidence,
            comparison=comparison,
            calculation=comparison.scenario,
        )
        return QueryResponse(
            route="what_if",
            answer=answer,
            evidence=evidence,
            calculation=comparison.scenario,
            comparison=comparison,
        )

    def answer(self, query: str, aid_input: AidInput | None = None) -> QueryResponse:
        route = classify_query(query, has_structured_inputs=aid_input is not None)
        evidence = self.retriever.search(query)
        calculation = None
        comparison: ScenarioComparison | None = None

        if route in {"calculation", "explanation"} and aid_input is not None:
            calculation = self.calculator.calculate(aid_input)
        elif route == "what_if" and aid_input is not None:
            comparison = self.calculator.compare_income_change(aid_input, income_delta=-5_000)
            calculation = comparison.scenario

        answer = self.explainer.generate(
            query=query,
            route=route,
            evidence=evidence,
            calculation=calculation,
            comparison=comparison,
        )
        return QueryResponse(
            route=route,
            answer=answer,
            evidence=evidence,
            calculation=calculation,
            comparison=comparison,
        )
