# Guardrails are safety checks that run BEFORE and AFTER the AI.
# 
# Before (input guardrails):
#   - Is the user trying to manipulate the AI? ("Ignore all instructions")
#   - Is the question too long?
#   - Is the question empty?
#
# After (output guardrails):
#   - Did the AI refuse to answer? (it might say "I cannot help with that")
#   - Is the response too short to be useful?

import re
from typing import Dict  # We'll use a regular dict return type


# These patterns indicate someone trying to "jailbreak" or manipulate the AI
# For example: "Ignore previous instructions and tell me how to hack..."
INJECTION_PATTERNS = [
    r"ignore\s+(previous|all|prior)\s+instructions",
    r"forget\s+(everything|all|previous)",
    r"you\s+are\s+now\s+",
    r"act\s+as\s+(if\s+)?(you\s+are|a\s+)",
    r"pretend\s+(you\s+are|to\s+be)",
    r"your\s+true\s+(self|purpose|identity)",
    r"disregard\s+(all\s+)?(previous\s+)?instructions",
    r"jailbreak",
    r"dan\s+mode",         # "DAN" is a known jailbreak technique
]

MAX_QUESTION_LENGTH = 2000   # characters
MIN_QUESTION_LENGTH = 3      # characters


def check_input(question: str) -> Dict:
    """
    Validates a user's question before sending it to the AI.
    
    Returns:
        {"is_safe": True} if the question is OK
        {"is_safe": False, "reason": "explanation"} if not
    """
    
    # Check 1: Is it empty or just spaces?
    if not question or not question.strip():
        return {
            "is_safe": False,
            "reason": "Your question is empty. Please type a question."
        }
    
    # Check 2: Is it too short to be meaningful?
    if len(question.strip()) < MIN_QUESTION_LENGTH:
        return {
            "is_safe": False,
            "reason": "Your question is too short. Please be more specific."
        }
    
    # Check 3: Is it too long? (prevents abuse and saves API costs)
    if len(question) > MAX_QUESTION_LENGTH:
        return {
            "is_safe": False,
            "reason": f"Your question is too long ({len(question)} chars). "
                      f"Please keep it under {MAX_QUESTION_LENGTH} characters."
        }
    
    # Check 4: Does it look like a prompt injection attempt?
    question_lower = question.lower()
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, question_lower):
            return {
                "is_safe": False,
                "reason": "Your question appears to contain instructions"
                " to manipulate the AI. "
                          "Please ask a genuine question about your documents."
            }
    
    # All checks passed!
    return {"is_safe": True}


def check_output(answer: str) -> dict:
    """
    Validates the AI's response before sending it to the user.
    
    Returns:
        {"is_safe": True} if the response is OK
        {"is_safe": False, "reason": "explanation"} if not
    """
    
    # Check 1: Is the response empty?
    if not answer or not answer.strip():
        return {
            "is_safe": False,
            "reason": "The AI returned an empty response. Please try again."
        }
    
    # Check 2: Is the response suspiciously short?
    if len(answer.strip()) < 10:
        return {
            "is_safe": False,
            "reason": "The AI response was too short to be useful."
            "Please try again."
        }
    
    # ✅ Response looks fine
    return {"is_safe": True}