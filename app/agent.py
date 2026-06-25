import os
import re

import google.auth
from google.adk.agents import LlmAgent
from google.adk.apps import App, ResumabilityConfig
from google.adk.events import Event, RequestInput
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from google.adk.workflow import Workflow, node
from mcp import StdioServerParameters



# Phase 3: Wire MCP Toolset using the Python SDK Server we built
mcp_toolset = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command="uv",
            args=["run", "python", "-m", "app.mcp_server"],
        ),
    ),
)

# Phase 4: Security Node in the Workflow Graph
@node
def security_checkpoint(node_input: str) -> Event:
    """
    Security check node designed to protect user privacy and system integrity.
    
    Implementation details:
    1. PII Redaction: Uses regex to identify and scrub sensitive info (Aadhaar, PAN, SSN, etc.)
       before it ever reaches the LLM, ensuring privacy compliance.
    2. Prompt Injection Defense: Checks input against known malicious patterns to prevent
       users from overriding agent instructions.
    
    Behaviors:
    - Returns route='safe' if the input is clean or successfully scrubbed.
    - Returns route='error' if malicious injection is detected, routing to the error handler.
    """
    pii_patterns = [
        (re.compile(r'\b\d{4}\s?\d{4}\s?\d{4}\b'), '[REDACTED_AADHAAR]'),
        (re.compile(r'\b[A-Z]{5}\d{4}[A-Z]{1}\b'), '[REDACTED_PAN]'),
        (re.compile(r'\+?\b\d{1,3}[\-\s]?\d{3,14}\b'), '[REDACTED_PHONE]'),
        (re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'), '[REDACTED_EMAIL]'),
        (re.compile(r'\b(?:\d[ -]*?){13,16}\b'), '[REDACTED_CC_OR_ID]'),
        (re.compile(r'\b\d{3}-\d{2}-\d{4}\b'), '[REDACTED_SSN]')
    ]
    injection_keywords = ["ignore previous instructions", "system prompt", "you are no longer", "forget instructions"]

    text_lower = node_input.lower()
    for keyword in injection_keywords:
        if keyword in text_lower:
            return Event(output="Security Error: Prompt injection attempt detected and blocked.", route="error")

    scrubbed = node_input
    for pattern, replacement in pii_patterns:
        scrubbed = pattern.sub(replacement, scrubbed)

    # Return the safe output to continue routing
    return Event(output=scrubbed, route="safe")


@node
def error_handler(node_input: str) -> Event:
    """
    Fallback node to handle security violations gracefully.
    If prompt injection is detected, this node intercepts the workflow
    and returns a clean error message to the user without executing downstream agents.
    """
    return Event(output=node_input)


from pydantic import BaseModel

class AnalystSummary(BaseModel):
    summary: str

class ClimatePlan(BaseModel):
    plan: str

# Phase 2: LlmAgent Sub-Agents
data_analyst_agent = LlmAgent(
    name="data_analyst_agent",
    model="gemini-2.5-flash",
    instruction=(
        "You are a Data Analyst Agent. Your job is to extract utility and usage data. "
        "Use the read_utility_data tool to fetch the raw usage numbers. "
        "If the user does not provide a file, default to 'dummy' for the file path to get realistic baseline data. "
        "CRITICAL: Summarize the data in 1 short sentence maximum to save API quota."
    ),
    description="Extracts and summarizes raw usage and utility data (electricity, transport, etc.)",
    tools=[mcp_toolset],
    output_schema=AnalystSummary,
    output_key="analyst_summary"
)

climate_impact_agent = LlmAgent(
    name="climate_impact_agent",
    model="gemini-2.5-flash",
    instruction=(
        "You are the Climate Impact & Motivation Agent. Your goal is to take the user's utility data "
        "and calculate their exact carbon footprint.\n\n"
        "1. Identify the user's location or region from the prompt. Use the get_emission_factors tool with the appropriate `region`.\n"
        "2. Multiply the user's usage by these factors to get the carbon footprint in kg CO2.\n\n"
        "CRITICAL FORMATTING RULES TO SAVE API QUOTA:\n"
        "- Output EXACTLY ONE SENTENCE (or one single line of text).\n"
        "- Include the kg CO2 breakdown by category (e.g., Electricity: X kg, Petrol: Y kg) and the Total footprint.\n"
        "- End with one brief reduction tip.\n"
        "- No headings, no bullet points, no greetings."
    ),
    description="Calculates exact carbon footprint, maps to ecological impacts, and creates a motivation plan for maximum of 2-3 lines to save API Quota",
    tools=[mcp_toolset],
    output_schema=ClimatePlan,
    output_key="final_plan"
)

# Human in the Loop (HITL) Node for Country Selection
@node(rerun_on_resume=True)
async def ask_country(ctx, node_input: str):
    """
    HITL node to interactively request the user's location.
    
    Design choice: Uses `rerun_on_resume=True` so that when the workflow resumes 
    with the user's input, this node re-executes and appends the explicit 
    country data to the payload before passing it to the Data Analyst.
    """
    if not ctx.resume_inputs:
        yield RequestInput(interrupt_id="ask_country", message="Before we calculate, which country or city are you in?")
        return
    
    country = ctx.resume_inputs["ask_country"]
    # Combine the original prompt with the user's explicit country selection
    combined_prompt = f"{node_input}\nUser's explicit region: {country}"
    yield Event(output=combined_prompt, route="next")

# Human in the Loop (HITL) Node for Final Approval
@node(rerun_on_resume=True)
async def human_approval(ctx, node_input: dict):
    """
    Final approval HITL node.
    
    Ensures that a human reviews the generated climate action plan before it is 
    finalized or executed, enforcing a safe, human-supervised AI pattern.
    """
    if not ctx.resume_inputs:
        yield RequestInput(interrupt_id="approval", message="Please review the plan. Type 'approve' to finalize.")
        return
    yield Event(output=f"User responded: {ctx.resume_inputs['approval']}\nFinal Plan: {node_input}", route="done")


# Phase 2: ADK 2.0 Workflow Graph Construction
workflow = Workflow(
    name="orchestrator",
    edges=[
        ('START', security_checkpoint),
        (security_checkpoint, {"safe": ask_country, "error": error_handler}),
        (ask_country, {"next": data_analyst_agent}),
        (data_analyst_agent, climate_impact_agent),
        (climate_impact_agent, human_approval),
    ]
)

# Define the App container
app = App(
    name="app",
    root_agent=workflow,
    resumability_config=ResumabilityConfig(is_resumable=True)
)
