import json
from typing import Any, Dict, List, TypedDict
from langchain_core.messages import HumanMessage
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END

import os
from dotenv import load_dotenv
load_dotenv()

# Centralized State
class AgentState(TypedDict):
    query: str
    user_id: str
    prior_user_turns: List[str]
    extracted_tickers: List[str]    
    next_node: str
    portfolio_data: Dict[str, Any]
    agent_outputs: Dict[str, Any]

# Updated function inside src/agentic_engine.py

def router_node(state: AgentState) -> Dict[str, Any]:
    llm = ChatGroq(model="llama-3.1-70b-versatile", temperature=0.0)
    
    # We explicitly tell the LLM to output ONLY raw JSON without wrapping it in markdown blocks
    system_prompt = (
        "You are the master routing engine for an investment app. Analyze the user's financial query, "
        "extract tickers (uppercase, e.g., 'AAPL'), and determine the target specialized agent string.\n\n"
        "Options:\n"
        "- 'portfolio_health': If they ask about holding returns, weights, concentration, or balance sheet.\n"
        "- 'market_news': If they ask about stock news, consensus, market articles, or buying/selling opinions.\n"
        "- 'tax_strategy': If they ask about harvesting gains, tax returns, capital distributions.\n\n"
        "CRITICAL: Output MUST be a valid JSON object ONLY. Do not include markdown formatting like ```json. "
        "Example format:\n"
        '{"agent": "market_news", "tickers": ["AAPL"]}'
    )
    
    try:
        response = llm.invoke([HumanMessage(content=f"{system_prompt}\n\nQuery: {state['query']}")])
        raw_text = response.content.strip()
        
        # Robust sanitization: strip any markdown JSON formatting blocks if the LLM included them anyway
        if "```" in raw_text:
            raw_text = raw_text.split("```")[1]
            if raw_text.startswith("json"):
                raw_text = raw_text[4:]
        raw_text = raw_text.strip()
        
        routing_data = json.loads(raw_text)
        agent = routing_data.get("agent", "portfolio_health")
        tickers = routing_data.get("tickers", [])
        
    except Exception as e:
        # Debug print inside your server log console to see what the LLM actually replied with
        print(f"[ROUTER ERROR] Parsing failed. Raw LLM content was: {response.content if 'response' in locals() else e}")
        agent = "portfolio_health"
        tickers = []
        
    return {"next_node": agent, "extracted_tickers": tickers}

def route_to_agent(state: AgentState) -> str:
    # Safely forward direction mapping target
    node = state.get("next_node", "portfolio_health")
    if node not in ["portfolio_health", "market_news", "tax_strategy"]:
        return "portfolio_health"
    return node

def compile_workflow():
    # Import inside to prevent cyclic path bindings
    from src.agents.agent_network import portfolio_health_node, market_news_node, tax_strategy_node
    
    workflow = StateGraph(AgentState)
    
    # Initialize computation nodes
    workflow.add_node("router", router_node)
    workflow.add_node("portfolio_health", portfolio_health_node)
    workflow.add_node("market_news", market_news_node)
    workflow.add_node("tax_strategy", tax_strategy_node)
    
    workflow.set_entry_point("router")
    
    # Setup state dynamic switches routing mappings
    workflow.add_conditional_edges(
        "router",
        route_to_agent,
        {
            "portfolio_health": "portfolio_health",
            "market_news": "market_news",
            "tax_strategy": "tax_strategy"
        }
    )
    
    # Direct agent completions straight to final termination state
    workflow.add_edge("portfolio_health", END)
    workflow.add_edge("market_news", END)
    workflow.add_edge("tax_strategy", END)
    
    return workflow.compile()