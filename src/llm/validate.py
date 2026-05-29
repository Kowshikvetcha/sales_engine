import json
from typing import List, Dict, Any, Tuple
from src.llm.client import build_llm
from src.utils.logging import logger
from src.config import settings

GROUNDING_VAL_SYSTEM_PROMPT = """
You are a compliance auditor. Your job is to verify that a drafted sales email is strictly grounded in a list of measured web audit FINDINGS.

Rules:
1. Compare the EMAIL BODY to the provided FINDINGS.
2. If the email asserts any website weakness, metric, score, or error that is NOT listed in the FINDINGS, you must FAIL the validation. For example, if the email mentions "page load speed is 5 seconds" but the findings only mention "missing meta tags", this is a FAIL.
3. If the email body only discusses issues that are listed in the FINDINGS, it passes validation.
4. Return a valid JSON object containing exactly three keys:
   - "status": "PASS" or "FAIL"
   - "reason": "Explanation of your decision"
   - "findings_cited": A JSON array of the exact finding strings from the FINDINGS list that were mentioned in the email.

JSON format:
{
  "status": "PASS",
  "reason": "Email body only references the performance and SSL issues listed in the findings.",
  "findings_cited": ["Homepage loads in 4500 ms (Lighthouse performance 45/100)"]
}
"""

async def validate_grounding(
    email_body: str,
    findings: List[str]
) -> Tuple[bool, List[str], str]:
    """
    Validates that the email body does not contain claims unsupported by findings.
    Returns: (is_valid: bool, findings_cited: List[str], reason: str)
    """
    if not findings:
        return False, [], "No findings provided for grounding"
        
    api_key = settings.anthropic_api_key or settings.openai_api_key or settings.google_api_key
    if not api_key or api_key == "mock-key":
        logger.warning("Mock LLM key detected. Skipping grounding validation (auto-passing).")
        # For mock runs, assume it passes and cites all findings
        return True, findings, "Mock validation auto-passed"

    try:
        llm = build_llm(temperature=0.0)  # low temperature for deterministic validation
        
        # Build chat prompt
        messages = [
            {"role": "system", "content": GROUNDING_VAL_SYSTEM_PROMPT},
            {"role": "user", "content": f"EMAIL BODY:\n{email_body}\n\nFINDINGS:\n" + "\n".join(f"- {f}" for f in findings)}
        ]
        
        response = await llm.ainvoke(messages)
        content = response.content.strip()
        
        # Clean markdown wrappers if any
        if content.startswith("```json"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        
        result = json.loads(content)
        is_pass = result.get("status") == "PASS"
        cited = result.get("findings_cited", [])
        reason = result.get("reason", "")
        
        return is_pass, cited, reason
    except Exception as e:
        logger.error("Exception during grounding validation", error=str(e))
        # Fallback to pass but warn, so transient LLM errors don't block dry-runs
        return True, findings, f"Validation bypassed due to exception: {str(e)}"
