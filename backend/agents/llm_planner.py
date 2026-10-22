
"""Optional OpenAI-compatible tool-calling planner.

Uses only Python's standard library. No API request is made unless
OPENAI_API_KEY is configured and this module is invoked.
"""

import json
import os
from urllib.request import Request, urlopen


def run_llm_tool_loop(analysis, tool_registry, max_calls=5):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured")

    model = os.getenv("DRILLINTEL_MODEL", "gpt-4.1-mini")

    tools = [
        {
            "type": "function",
            "function": {
                "name": name,
                "description": (
                    "Inspect the existing well analysis and report "
                    "evidence relevant to drilling decision support."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "additionalProperties": False,
                },
                "strict": True,
            },
        }
        for name in tool_registry
    ]

    messages = [
        {
            "role": "system",
            "content": (
                "You are DrillIntel, a drilling decision-support assistant. "
                "Choose tools based on evidence gaps. Inspect risk, offsets, "
                "historical events, and recommendations as appropriate. "
                "Do not invent findings. Never issue drilling commands. "
                "Require qualified human review. Finish with a concise "
                "summary of checks performed and remaining evidence gaps."
            ),
        },
        {
            "role": "user",
            "content": (
                "Review this analysis. Select the most useful available "
                "inspection tools, then summarize the evidence and gaps. "
                "Analysis JSON:\n"
                + json.dumps(analysis, default=str)[:18000]
            ),
        },
    ]

    steps = []
    findings = {}

    for _ in range(max_calls):
        payload = {
            "model": model,
            "messages": messages,
            "tools": tools,
            "tool_choice": "auto",
        }

        request = Request(
            "https://api.openai.com/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        with urlopen(request, timeout=45) as response:
            result = json.loads(response.read().decode("utf-8"))

        message = result["choices"][0]["message"]
        messages.append(message)

        tool_calls = message.get("tool_calls", [])
        if not tool_calls:
            return {
                "steps": steps,
                "findings": findings,
                "summary": message.get("content", ""),
                "model": model,
            }

        for call in tool_calls:
            name = call["function"]["name"]

            if name not in tool_registry:
                output = {"error": "Tool is not permitted"}
            else:
                output = tool_registry[name](analysis)
                findings[name] = output

                steps.append({
                    "stage": name,
                    "name": name.replace("_", " ").title(),
                    "status": "complete",
                    "tool": name,
                    "reason": "Selected by the LLM based on the current evidence.",
                    "detail": output.get("finding", ""),
                    "result": output,
                })

            messages.append({
                "role": "tool",
                "tool_call_id": call["id"],
                "content": json.dumps(output, default=str),
            })

    return {
        "steps": steps,
        "findings": findings,
        "summary": "Tool-call limit reached; human review is required.",
        "model": model,
    }
