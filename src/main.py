from dotenv import load_dotenv
load_dotenv()  # Auto load root environment elements before initializing bindings

import asyncio
import json
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List
from langchain_core.messages import HumanMessage, AIMessage

from src.safety.guard import check as perform_safety_evaluation
from src.agentic_engine import compile_workflow

app = FastAPI(title="Valura AI Enterprise Production Agentic Backend")
runnable_graph = compile_workflow()

class ChatPayload(BaseModel):
    query: str
    user_id: str
    session_id: str = Field(default="default_session_thread") 

@app.post("/api/chat")
async def stream_chat_endpoint(payload: ChatPayload):
    async def sse_event_streamer():
        # Step A: Pre-LLM Local Safety evaluation
        safety_output = perform_safety_evaluation(payload.query)
        is_safe = not safety_output.blocked 
        
        yield f"event: pipeline_status\ndata: {json.dumps({'status': 'passed_safety' if is_safe else 'failed_safety'})}\n\n"
        await asyncio.sleep(0.02)
        
        if not is_safe:
            yield f"event: done\ndata: {json.dumps({'status': 'blocked_by_compliance', 'reason': safety_output.message})}\n\n"
            return
            
        # Registering the State Config settings target mapping for LangGraph Memory Saver checkpointing
        graph_config = {"configurable": {"thread_id": f"{payload.user_id}_{payload.session_id}"}}
        
        initial_state = {
            "query": payload.query,
            "user_id": payload.user_id,
            "messages": [],
            "extracted_tickers": [],
            "next_node": "",
            "agent_outputs": {},
            "final_response": ""
        }
        
        # Async streaming loop iteration layer
        current_agent = "unknown"
        final_text_response = "Unable to compile full response blocks."
        
        async for output in runnable_graph.astream(initial_state, config=graph_config):
            if "router" in output:
                current_agent = output["router"].get("next_node", "unknown")
                yield f"event: classification\ndata: {json.dumps({'intent': current_agent, 'agent': current_agent, 'entities': {'tickers': output['router'].get('extracted_tickers', [])}})}\n\n"
                await asyncio.sleep(0.02)
                
            elif current_agent in output:
                agent_payload = output[current_agent].get("agent_outputs", {})
                yield f"event: agent_response\ndata: {json.dumps({'agent': current_agent, 'payload': agent_payload})}\n\n"
                await asyncio.sleep(0.02)
                
            elif "synthesizer" in output:
                final_text_response = output["synthesizer"].get("final_response", "")
                
        yield f"event: final_insight\ndata: {json.dumps({'response': final_text_response})}\n\n"
        await asyncio.sleep(0.02)
        
        await runnable_graph.aupdate_state(
            graph_config,
            {"messages": [HumanMessage(content=payload.query), AIMessage(content=final_text_response)]}
        )
        
        yield "event: done\ndata: " + '{"status": "completed"}' + "\n\n"

    return StreamingResponse(sse_event_streamer(), media_type="text/event-stream")