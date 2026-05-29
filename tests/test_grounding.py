import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.llm.validate import validate_grounding

@pytest.mark.asyncio
async def test_validate_grounding_pass():
    # Setup findings
    findings = [
        "Homepage loads in 4500 ms (Lighthouse performance 45/100)",
        "No lead-capture form found; inquiries rely on a raw email link"
    ]
    email_body = "Hi there, I saw your homepage loads slow (taking 4.5 seconds) and there is no contact form."
    
    # Mock LLM response representing validation success
    mock_llm = MagicMock()
    mock_response = MagicMock()
    mock_response.content = (
        '{"status": "PASS", "reason": "Only cites performance and form findings", '
        '"findings_cited": ["Homepage loads in 4500 ms (Lighthouse performance 45/100)", '
        '"No lead-capture form found; inquiries rely on a raw email link"]}'
    )
    mock_llm.ainvoke = AsyncMock(return_value=mock_response)
    
    with patch("src.llm.validate.build_llm", return_value=mock_llm), \
         patch("src.llm.validate.settings") as mock_settings:
        # Force validator to run by providing a dummy key
        mock_settings.anthropic_api_key = "live-key-simulated"
        
        is_pass, cited, reason = await validate_grounding(email_body, findings)
        
        assert is_pass is True
        assert len(cited) == 2
        assert findings[0] in cited
        assert findings[1] in cited

@pytest.mark.asyncio
async def test_validate_grounding_fail():
    findings = [
        "Homepage loads in 4500 ms (Lighthouse performance 45/100)"
    ]
    # Email body contains ungrounded claim about SSL certificates
    email_body = "Hi, I noticed your page loads slow and you do not have an SSL certificate."
    
    # Mock LLM response representing validation failure
    mock_llm = MagicMock()
    mock_response = MagicMock()
    mock_response.content = (
        '{"status": "FAIL", "reason": "Email cites missing SSL certificate which is not in findings", '
        '"findings_cited": ["Homepage loads in 4500 ms (Lighthouse performance 45/100)"]}'
    )
    mock_llm.ainvoke = AsyncMock(return_value=mock_response)
    
    with patch("src.llm.validate.build_llm", return_value=mock_llm), \
         patch("src.llm.validate.settings") as mock_settings:
        mock_settings.anthropic_api_key = "live-key-simulated"
        
        is_pass, cited, reason = await validate_grounding(email_body, findings)
        
        assert is_pass is False
        assert "SSL certificate" in reason
        assert len(cited) == 1
