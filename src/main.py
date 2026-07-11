# src/main.py

import asyncio
import json
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List

# FIXED IMPORT: We target the correct module 'check' functional pointer mapping
from src.safety.guard import check as perform_safety_evaluation
from src.agentic_engine import compile_workflow

app = FastAPI(title="Valura AI Agentic Backend Hub Engine")
runnable_graph = compile_workflow()

class ChatPayload(BaseModel):
    query: str
    user_id: str
    prior_user_turns: List[str] = Field(default_factory=list)

@app.post("/api/chat")
async def stream_chat_endpoint(payload: ChatPayload):
    async def sse_event_streamer():
        # Step A: Trigger Local Safety Evaluation Node pipeline execution
        safety_output = perform_safety_evaluation(payload.query)
        
        # FIXED CHECK: safety_output has 'blocked' boolean flag property attribute
        is_safe = not safety_output.blocked 
        
        yield f"event: pipeline_status\ndata: {json.dumps({'status': 'passed_safety' if is_safe else 'failed_safety'})}\n\n"
        await asyncio.sleep(0.05)
        
        if not is_safe:
            yield f"event: done\ndata: {json.dumps({'status': 'blocked_by_compliance', 'reason': safety_output.message})}\n\n"
            return
            
        # Step B: Hydrate core initialization variables for LangGraph State Mapping
        initial_state = {
            "query": payload.query,
            "user_id": payload.user_id,
            "prior_user_turns": payload.prior_user_turns,
            "extracted_tickers": [],
            "next_node": "",
            "portfolio_data": {},
            "agent_outputs": {}
        }
        
        # Step C: Stream graph steps sequentially inside async event loops
        current_agent = "unknown"
        
        for output in runnable_graph.stream(initial_state):
            if "router" in output:
                current_agent = output["router"].get("next_node", "unknown")
                yield f"event: classification\ndata: {json.dumps({'intent': current_agent, 'agent': current_agent, 'entities': {'tickers': output['router'].get('extracted_tickers', [])}})}\n\n"
                await asyncio.sleep(0.05)
                
            elif current_agent in output:
                agent_payload = output[current_agent].get("agent_outputs", {})
                yield f"event: agent_response\ndata: {json.dumps({'agent': current_agent, 'payload': agent_payload})}\n\n"
                await asyncio.sleep(0.05)
                
        yield "event: done\ndata: {" + '"status": "completed"' + "}\n\n"

    return StreamingResponse(sse_event_streamer(), media_type="text/event-stream")