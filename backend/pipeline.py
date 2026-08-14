import asyncio
import json
import logging
from typing import Dict, List, Optional, Tuple

from backend.config import settings
from backend.llm_client import GroqLLMClient
from backend.models import (
    AdjudicationAssessment,
    ClaimMatrixEntry,
    CouncilResponse,
    ExtractedInformation,
    FinalSafetyCheck,
    ModelDeliberationDetail,
    ResponseAssessment,
    RouterClassification,
    SafetyClassification,
    Source,
)
from backend.prompts import (
    CLAIM_EVALUATION_PROMPT,
    CLAIM_EXTRACTION_PROMPT,
    CRITIQUE_PROMPT,
    EVIDENCE_SEARCH_PROMPT,
    EXTRACTION_SYSTEM_PROMPT,
    FINAL_SAFETY_PROMPT,
    MODEL_1_CLINICAL_ANALYST_PROMPT,
    MODEL_2_SKEPTICAL_ANALYST_PROMPT,
    MODEL_3_ADJUDICATOR_PROMPT,
    REVISION_PROMPT,
    ROUTER_SYSTEM_PROMPT,
    SAFETY_SYSTEM_PROMPT,
    SIMPLE_GENERAL_PROMPT,
)

logger = logging.getLogger(__name__)
FINAL_SAFETY_TIMEOUT_SECONDS = 30


def _get_llm_client() -> GroqLLMClient:
    return GroqLLMClient(api_key=settings.groq_api_key)


async def _safe_model_call(coro, model_name: str) -> Tuple[Optional[str], bool]:
    """Wraps an async model call with error handling for graceful degradation.
    Returns (result_text, success_bool)."""
    try:
        result = await coro
        return result, True
    except Exception as e:
        logger.error(f"{model_name} call failed completely: {e}")
        return None, False


async def _run_claim_evidence_pass(
    client: GroqLLMClient,
    combined_analyses: str,
    info_context: str,
) -> Tuple[List[ClaimMatrixEntry], List[Source], str]:
    """Runs a full claim-extraction + evidence-retrieval + evaluation pass.
    Returns (parsed_claims, parsed_sources, evidence_matrix_summary_json)."""

    # Step 1: Extract claims from analyses
    try:
        claims_extraction_resp = await client.chat_json(
            messages=[
                {"role": "system", "content": CLAIM_EXTRACTION_PROMPT},
                {"role": "user", "content": combined_analyses},
            ],
            model=settings.model_model1,
            temperature=0.1,
        )
        extracted_claims_list = claims_extraction_resp.get("claims", [])
    except Exception as exc:
        logger.warning(f"Claim extraction failed: {exc}")
        extracted_claims_list = []

    claims_text_summary = json.dumps(extracted_claims_list, indent=2)

    if not extracted_claims_list:
        return [], [], "[]"

    # Step 2: Call A — Browser Search for real evidence
    retrieved_web_content = ""
    try:
        search_result = await client.chat_with_browser_search(
            messages=[
                {
                    "role": "system",
                    "content": EVIDENCE_SEARCH_PROMPT.format(
                        claims_text=claims_text_summary
                    ),
                },
                {
                    "role": "user",
                    "content": f"Find evidence for patient scenario:\n{info_context}",
                },
            ],
            model=settings.model_model1,
            temperature=0.3,
            reasoning_effort="medium",
        )
        retrieved_web_content = search_result.get("content", "")
    except Exception as exc:
        logger.warning(f"Browser evidence search failed: {exc}")

    # Step 3: Call B — Structured Claim-Evidence Matrix Evaluation
    eval_user_msg = f"""Extracted Claims:
{claims_text_summary}

Retrieved Search Evidence:
{retrieved_web_content}
"""

    try:
        evidence_eval_resp = await client.chat_json(
            messages=[
                {"role": "system", "content": CLAIM_EVALUATION_PROMPT},
                {"role": "user", "content": eval_user_msg},
            ],
            model=settings.model_model1,
            temperature=0.1,
        )

        evaluated_claims_data = evidence_eval_resp.get("evaluated_claims", [])
        sources_data = evidence_eval_resp.get("sources", [])

        parsed_claims = [ClaimMatrixEntry(**c) for c in evaluated_claims_data]
        parsed_sources = [Source(**s) for s in sources_data]
    except Exception as exc:
        logger.warning(f"Evidence evaluation failed: {exc}")
        parsed_claims = [
            ClaimMatrixEntry(
                claim_id=claim.get("claim_id", "C000"),
                text=claim.get("text", ""),
                claim_type=claim.get("claim_type", "OTHER"),
                importance=claim.get("importance", "LOW"),
                status="INSUFFICIENT_EVIDENCE",
                overall_evidence_quality="VERY_LOW",
                reasoning="Evidence verification could not be completed due to a retrieval or parsing error.",
                source_ids=[],
            )
            for claim in extracted_claims_list
        ]
        parsed_sources = []
        evaluated_claims_data = [claim.model_dump() for claim in parsed_claims]

    evidence_matrix_summary = json.dumps(evaluated_claims_data, indent=2)

    return parsed_claims, parsed_sources, evidence_matrix_summary


async def run_council(prompt: str) -> CouncilResponse:
    client = _get_llm_client()
    phases_completed = []

    # ----------------------------------------------------
    # Phase 1: Safety Classification & Routing
    # ----------------------------------------------------
    phases_completed.append("safety_and_routing")

    # Run Safety Classifier & Router concurrently
    safety_data_task = client.chat_json(
        messages=[
            {"role": "system", "content": SAFETY_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        model=settings.model_safety,
        pydantic_model=SafetyClassification,
        temperature=0.1,
        reasoning_effort="medium",
    )

    router_data_task = client.chat_json(
        messages=[
            {"role": "system", "content": ROUTER_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        model=settings.model_router,
        pydantic_model=RouterClassification,
        temperature=0.1,
        reasoning_effort="low",
    )

    safety_dict, router_dict = await asyncio.gather(
        safety_data_task, router_data_task
    )

    safety = SafetyClassification(**safety_dict)
    router = RouterClassification(**router_dict)

    # Safety override handling
    route_category = router.category
    if safety.risk_level in ["urgent", "emergency"] or safety.route_override:
        if safety.risk_level == "emergency":
            route_category = "EMERGENCY"
        else:
            route_category = "URGENT_MEDICAL"

    # ----------------------------------------------------
    # Path A: Fast Simple/General Medical Answer
    # ----------------------------------------------------
    if route_category in ["SIMPLE_MEDICAL", "GENERAL"] and safety.risk_level in [
        "safe",
        "caution",
    ]:
        phases_completed.append("simple_answer")
        simple_answer = await client.chat(
            messages=[
                {"role": "system", "content": SIMPLE_GENERAL_PROMPT},
                {"role": "user", "content": prompt},
            ],
            model=settings.model_simple,
            temperature=settings.temperature,
        )

        return CouncilResponse(
            prompt=prompt,
            route=route_category,
            safety=safety,
            answer=simple_answer,
            assessment=ResponseAssessment(
                certainty="likely",
                evidence_quality="moderate",
            ),
            recommendations=[
                "For personalized medical concerns or changing symptoms, consult a qualified healthcare provider."
            ],
            missing_information=[],
            extracted_information=None,
            claims=[],
            sources=[],
            uncertainties=[],
            model_details=None,
            final_safety=None,
            phases_completed=phases_completed,
        )

    # ----------------------------------------------------
    # Path B: Full Evidence-Grounded Medical Deliberation
    # ----------------------------------------------------
    # 1. Relevant Information Extraction
    phases_completed.append("information_extraction")
    extracted_dict = await client.chat_json(
        messages=[
            {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        model=settings.model_router,
        pydantic_model=ExtractedInformation,
        temperature=0.1,
    )
    extracted_info = ExtractedInformation(**extracted_dict)

    # Format clinical context string
    info_context = f"""User Request: {prompt}
Extracted Symptoms: {', '.join(extracted_info.symptoms) or 'None specified'}
Duration: {extracted_info.duration or 'Unspecified'}
Severity: {extracted_info.severity or 'Unspecified'}
Report Values / Labs: {', '.join(extracted_info.report_values) or 'None'}
Medications: {', '.join(extracted_info.medications) or 'None'}
History: {', '.join(extracted_info.history) or 'None'}
Missing Info: {', '.join(extracted_info.missing_information) or 'None'}
Ambiguous Info: {', '.join(extracted_info.ambiguous_information) or 'None'}
Unreadable Info: {', '.join(extracted_info.unreadable_information) or 'None'}
"""

    # 2. Model 1 & Model 2 Concurrent Initial Analysis (with graceful degradation)
    phases_completed.append("dual_model_analysis")

    m1_task = _safe_model_call(
        client.chat(
            messages=[
                {"role": "system", "content": MODEL_1_CLINICAL_ANALYST_PROMPT},
                {"role": "user", "content": info_context},
            ],
            model=settings.model_model1,
            temperature=0.4,
            reasoning_effort="medium",
        ),
        "Model 1 (Clinical Analyst)",
    )

    m2_task = _safe_model_call(
        client.chat(
            messages=[
                {"role": "system", "content": MODEL_2_SKEPTICAL_ANALYST_PROMPT},
                {"role": "user", "content": info_context},
            ],
            model=settings.model_model2,
            temperature=0.4,
            reasoning_effort="medium",
        ),
        "Model 2 (Skeptical Analyst)",
    )

    (m1_initial, m1_ok), (m2_initial, m2_ok) = await asyncio.gather(m1_task, m2_task)

    # §26 Graceful degradation: if both fail, return an error-state response
    if not m1_ok and not m2_ok:
        return CouncilResponse(
            prompt=prompt,
            route=route_category,
            safety=safety,
            answer="Both clinical analysis models were temporarily unavailable. Please try again in a few moments. If you are experiencing a medical emergency, please call emergency services immediately.",
            assessment=ResponseAssessment(
                certainty="cannot_determine",
                evidence_quality="insufficient",
            ),
            recommendations=["Please retry your query shortly.", "For urgent concerns, consult a healthcare provider directly."],
            missing_information=[],
            extracted_information=extracted_info if 'extracted_info' in locals() else None,
            claims=[],
            sources=[],
            uncertainties=[],
            model_details=None,
            final_safety=None,
            phases_completed=phases_completed,
        )

    # If only one model failed, use the successful one for both roles (single-model degradation)
    single_model_mode = False
    if not m1_ok:
        logger.warning("Model 1 failed. Proceeding with single-model (Model 2) analysis at reduced confidence.")
        m1_initial = m2_initial
        single_model_mode = True
    elif not m2_ok:
        logger.warning("Model 2 failed. Proceeding with single-model (Model 1) analysis at reduced confidence.")
        m2_initial = m1_initial
        single_model_mode = True

    # 3. Layer 6: Initial Claim Extraction & Evidence Retrieval
    phases_completed.append("evidence_retrieval")

    combined_analyses = f"MODEL 1 (CLINICAL ANALYST):\n{m1_initial}\n\nMODEL 2 (SKEPTICAL ANALYST):\n{m2_initial}"

    initial_claims, initial_sources, initial_evidence_matrix = await _run_claim_evidence_pass(
        client, combined_analyses, info_context
    )

    # 4. Peer Review (Critique Phase)
    phases_completed.append("peer_review")

    if single_model_mode:
        # In single-model mode, skip peer critique (no independent second opinion)
        m1_critique = "Single-model mode: peer critique unavailable (one model was temporarily unavailable)."
        m2_critique = m1_critique
    else:
        m1_critique_task = _safe_model_call(
            client.chat(
                messages=[
                    {"role": "system", "content": CRITIQUE_PROMPT},
                    {
                        "role": "user",
                        "content": f"Please critique Model 2's assessment.\n\nModel 2 Initial Analysis:\n{m2_initial}\n\nEvidence Matrix:\n{initial_evidence_matrix}",
                    },
                ],
                model=settings.model_model1,
                temperature=0.3,
            ),
            "Model 1 Critique",
        )

        m2_critique_task = _safe_model_call(
            client.chat(
                messages=[
                    {"role": "system", "content": CRITIQUE_PROMPT},
                    {
                        "role": "user",
                        "content": f"Please critique Model 1's assessment.\n\nModel 1 Initial Analysis:\n{m1_initial}\n\nEvidence Matrix:\n{initial_evidence_matrix}",
                    },
                ],
                model=settings.model_model2,
                temperature=0.3,
            ),
            "Model 2 Critique",
        )

        (m1_critique, m1c_ok), (m2_critique, m2c_ok) = await asyncio.gather(
            m1_critique_task, m2_critique_task
        )
        if not m1c_ok:
            m1_critique = "Critique unavailable due to temporary model error."
        if not m2c_ok:
            m2_critique = "Critique unavailable due to temporary model error."

    # 5. Re-Evaluation (Revision Phase)
    phases_completed.append("re_evaluation")

    if single_model_mode:
        # Single-model: skip revision, use initial analysis as revised
        m1_revised = m1_initial
        m2_revised = m2_initial
    else:
        m1_revise_task = _safe_model_call(
            client.chat(
                messages=[
                    {"role": "system", "content": "You are Model 1: Clinical Analyst."},
                    {
                        "role": "user",
                        "content": REVISION_PROMPT.format(
                            own_analysis=m1_initial,
                            critique=m2_critique,
                            evidence_matrix=initial_evidence_matrix,
                        ),
                    },
                ],
                model=settings.model_model1,
                temperature=0.3,
            ),
            "Model 1 Revision",
        )

        m2_revise_task = _safe_model_call(
            client.chat(
                messages=[
                    {"role": "system", "content": "You are Model 2: Skeptical Analyst."},
                    {
                        "role": "user",
                        "content": REVISION_PROMPT.format(
                            own_analysis=m2_initial,
                            critique=m1_critique,
                            evidence_matrix=initial_evidence_matrix,
                        ),
                    },
                ],
                model=settings.model_model2,
                temperature=0.3,
            ),
            "Model 2 Revision",
        )

        (m1_revised, m1r_ok), (m2_revised, m2r_ok) = await asyncio.gather(
            m1_revise_task, m2_revise_task
        )
        if not m1r_ok:
            m1_revised = m1_initial  # fallback to initial if revision fails
        if not m2r_ok:
            m2_revised = m2_initial

    # 6. §14 FINAL CLAIM MATRIX — Re-run claim-evidence verification on revised analyses
    # The claims may have changed after peer review, so we must re-verify.
    phases_completed.append("final_claim_matrix")

    revised_combined = f"MODEL 1 (CLINICAL ANALYST — REVISED):\n{m1_revised}\n\nMODEL 2 (SKEPTICAL ANALYST — REVISED):\n{m2_revised}"

    try:
        final_claims, final_sources, final_evidence_matrix = await _run_claim_evidence_pass(
            client, revised_combined, info_context
        )
    except Exception as e:
        logger.warning(f"Final claim matrix re-verification failed: {e}. Using initial evidence matrix.")
        final_claims = initial_claims
        final_sources = initial_sources
        final_evidence_matrix = initial_evidence_matrix

    # 7. Model 3: Final Evidence Adjudication
    phases_completed.append("final_adjudication")
    adjudication_input = f"""Patient Case Context:
{info_context}

Model 1 (Clinical Analyst) Revised Analysis:
{m1_revised}

Model 2 (Skeptical Analyst) Revised Analysis:
{m2_revised}

Model 1 Critique of Model 2:
{m1_critique}

Model 2 Critique of Model 1:
{m2_critique}

Verified FINAL Evidence Matrix:
{final_evidence_matrix}
"""

    if single_model_mode:
        adjudication_input += "\n\nIMPORTANT NOTE: This analysis was performed in single-model degraded mode because one clinical analyst was temporarily unavailable. State this limitation and reduce certainty accordingly.\n"

    adj_dict = await client.chat_json(
        messages=[
            {"role": "system", "content": MODEL_3_ADJUDICATOR_PROMPT},
            {"role": "user", "content": adjudication_input},
        ],
        model=settings.model_model3,
        pydantic_model=AdjudicationAssessment,
        temperature=0.2,
        reasoning_effort="high",
    )

    adjudication = AdjudicationAssessment(**adj_dict)

    # 8. Final Safety Gate Audit
    phases_completed.append("final_safety_gate")
    try:
        final_safety_dict = await asyncio.wait_for(
            client.chat_json(
                messages=[
                    {"role": "system", "content": FINAL_SAFETY_PROMPT},
                    {
                        "role": "user",
                        "content": f"User Prompt: {prompt}\nAdjudicated Answer:\n{adjudication.answer}\nRisk Level: {safety.risk_level}",
                    },
                ],
                model=settings.model_safety,
                pydantic_model=FinalSafetyCheck,
                temperature=0.1,
            ),
            timeout=FINAL_SAFETY_TIMEOUT_SECONDS,
        )
        final_safety = FinalSafetyCheck(**final_safety_dict)
    except asyncio.TimeoutError:
        logger.warning(
            "Final safety gate timed out after %s seconds; falling back to prior safety classification.",
            FINAL_SAFETY_TIMEOUT_SECONDS,
        )
        fallback_level = safety.risk_level if safety.risk_level in ["urgent", "emergency"] else "caution" if safety.risk_level == "caution" else "safe"
        final_safety = FinalSafetyCheck(
            risk_level=fallback_level,
            safety_notice="Final safety review timed out; using the earlier safety classification.",
            must_seek_emergency=fallback_level == "emergency",
        )
    except Exception as exc:
        logger.warning(
            "Final safety gate failed: %s; falling back to prior safety classification.",
            exc,
        )
        fallback_level = safety.risk_level if safety.risk_level in ["urgent", "emergency"] else "caution" if safety.risk_level == "caution" else "safe"
        final_safety = FinalSafetyCheck(
            risk_level=fallback_level,
            safety_notice="Final safety review was unavailable; using the earlier safety classification.",
            must_seek_emergency=fallback_level == "emergency",
        )

    # Update safety notice if emergency/urgent
    final_safety_level = final_safety.risk_level
    if safety.risk_level in ["urgent", "emergency"]:
        final_safety_level = safety.risk_level

    updated_safety = SafetyClassification(
        risk_level=final_safety_level,
        route_override=safety.route_override,
        red_flags=safety.red_flags,
        reason=final_safety.safety_notice or safety.reason,
    )

    final_answer = adjudication.answer.strip()
    if final_safety.safety_notice.strip():
        final_answer = f"{final_safety.safety_notice.strip()}\n\n{final_answer}".strip()
    elif final_safety_level == "emergency":
        final_answer = (
            "Emergency medical attention is recommended immediately. If you are in immediate danger, call emergency services now.\n\n"
            + final_answer
        ).strip()
    elif final_safety_level == "urgent":
        final_answer = (
            "Prompt medical evaluation is recommended. Seek urgent clinical care today if symptoms are ongoing or worsening.\n\n"
            + final_answer
        ).strip()

    model_details = {
        "model_1": ModelDeliberationDetail(
            model_name="Model 1: Clinical Analyst",
            model_id=settings.model_model1,
            initial_analysis=m1_initial,
            critique_given=m1_critique,
            critique_received=m2_critique,
            revised_analysis=m1_revised,
            was_revised=m1_revised.strip() != m1_initial.strip(),
        ),
        "model_2": ModelDeliberationDetail(
            model_name="Model 2: Skeptical Analyst",
            model_id=settings.model_model2,
            initial_analysis=m2_initial,
            critique_given=m2_critique,
            critique_received=m1_critique,
            revised_analysis=m2_revised,
            was_revised=m2_revised.strip() != m2_initial.strip(),
        ),
    }

    return CouncilResponse(
        prompt=prompt,
        route=route_category,
        safety=updated_safety,
        answer=final_answer,
        assessment=ResponseAssessment(
            certainty=adjudication.certainty,
            evidence_quality=adjudication.evidence_quality,
        ),
        recommendations=adjudication.recommendations,
        missing_information=adjudication.missing_information,
        extracted_information=extracted_info,
        claims=final_claims,
        sources=final_sources,
        uncertainties=adjudication.uncertainties,
        model_details=model_details,
        final_safety=final_safety,
        phases_completed=phases_completed,
    )
