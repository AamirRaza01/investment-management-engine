import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, Request
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

# Pipeline imports
from src.safety.guard import check as check_safety
from src.classifier.classifier import classify
from src.agents.portfolio_health import run as run_portfolio_health
from src.utils.user_loader import load_user_profile

# Initialize Logging and FastAPI App
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ValuraEngine")

app = FastAPI(
    title="Valura AI — Investment Management Engine",
    description="The spine layer hosting safety filters, intent routing, and portfolio diagnostic agents."
)

# --- Pydantic Request Contract Schemas ---
class ChatQueryRequest(BaseModel):
    query: str = Field(..., description="The fresh financial text question from the client.")
    user_id: str = Field(..., description="The unique identity token of the user profile.")
    prior_user_turns: List[str] = Field(default_factory=list, description="Historical list of user text entries.")

# --- The Streaming Core Stream Generator ---
async def pipeline_stream_generator(request_payload: ChatQueryRequest):
    """
    Orchestrates the lifecycle of an asset inquiry request step-by-step:
    Safety Guard Filter -> Intent Classifier -> Agent Router Execution -> SSE Streams.
    """
    try:
        # Phase 1: Execution of the Synchronous Local Safety Guard
        logger.info(f"Processing safety evaluation for query: '{request_payload.query}'")
        safety_verdict = check_safety(request_payload.query)
        
        if safety_verdict.blocked:
            logger.warning(f"Query blocked under category: {safety_verdict.category}")
            yield {
                "event": "safety_block",
                "data": json.dumps({
                    "status": "blocked",
                    "category": safety_verdict.category,
                    "message": safety_verdict.message
                })
            }
            return  # Terminate streaming flow cleanly immediately following safety interception

        # Notify user that safety verification cleared successfully
        yield {
            "event": "pipeline_status",
            "data": json.dumps({"status": "passed_safety"})
        }
        await asyncio.sleep(0.1)  # Minimal buffer to ensure smooth packet transmission stream

        # Phase 2: Intent Classification & Parameter Parsing
        logger.info("Executing probabilistic text intent classification...")
        classification = classify(request_payload.query)
        
        yield {
            "event": "classification",
            "data": json.dumps({
                "intent": classification.intent,
                "agent": classification.agent,
                "entities": classification.entities
            })
        }
        await asyncio.sleep(0.1)

        # Phase 3: Route Request to Dedicated Agents or Stubs
        target_agent = classification.agent

        if target_agent == "portfolio_health":
            logger.info(f"Routing request to Portfolio Health Agent for user: {request_payload.user_id}")
            
            # Fetch profile data out of local fixture files
            user_profile = load_user_profile(request_payload.user_id)
            if not user_profile:
                # If profile is missing, fallback safely using an empty structure to prevent crashes
                user_profile = {"user_id": request_payload.user_id, "positions": [], "preferences": {}}

            # Run analytical engine calculations
            health_report = run_portfolio_health(user_profile)
            
            yield {
                "event": "agent_response",
                "data": json.dumps({
                    "agent": "portfolio_health",
                    "payload": health_report
                })
            }

        else:
            # Stub contract for non-portfolio agents
            logger.info(f"Routing to unimplemented agent stub: '{target_agent}'")
            yield {
                "event": "agent_stub",
                "data": json.dumps({
                    "classified_intent": classification.intent,
                    "extracted_entities": classification.entities,
                    "agent": target_agent,
                    "message": f"The '{target_agent}' agent is successfully mapped in the routing table, but is not fully active in this iteration build."
                })
            }

        # Signify final data channel closure sequence
        yield {
            "event": "done",
            "data": json.dumps({"status": "completed"})
        }

    except asyncio.CancelledError:
        logger.info("Streaming connection prematurely disconnected by client.")
    except Exception as exc:
        logger.error(f"Unexpected operational error within the application spine pipeline: {str(exc)}")
        yield {
            "event": "error",
            "data": json.dumps({
                "error_code": "INTERNAL_PIPELINE_ERROR",
                "message": "An unhandled calculation error occurred. Channel closing down safely."
            })
        }

# --- HTTP Web Endpoint Routing ---
@app.post("/api/chat")
async def stream_chat_interactions(payload: ChatQueryRequest, request: Request):
    """
    Accepts text payload inquiries and provisions an open Server-Sent Events channel stream.
    No fallback plain JSON response pathways exist.
    """
    event_generator = pipeline_stream_generator(payload)
    # Wrap standard Python iterable yield data structures with server event protocols
    return EventSourceResponse(event_generator)