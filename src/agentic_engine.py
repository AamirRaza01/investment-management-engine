import json
import os
from typing import Any, Dict, List, TypedDict
from langchain_core.messages import HumanMessage, SystemMessage, BaseMessage
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from dotenv import load_dotenv

load_dotenv()

class AgentState(TypedDict):
    query: str
    user_id: str
    messages: List[BaseMessage]        # Native Multi-Turn Message Cache tracking
    extracted_tickers: List[str]
    next_node: str
    agent_outputs: Dict[str, Any]      
    final_response: str                # Human-friendly structured answer

# 1. Supervisor Intent Routing Node
def router_node(state: AgentState) -> Dict[str, Any]:
    api_key = os.getenv("GROQ_API_KEY")
    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.0, groq_api_key=api_key)
    
    system_prompt = (
        "You are the master routing engine. Analyze the user's latest message, "
        "extract stock tickers (uppercase, e.g., 'AAPL'), and determine the target specialized agent string.\n\n"
        "Options:\n"
        "- 'portfolio_health': Queries regarding holding metrics, balances, diversification checks, concentrations.\n"
        "- 'market_news': Queries regarding fresh news, asset consensus, opinions, market trends.\n"
        "- 'tax_strategy': Queries regarding tax harvesting, returns optimizations, capital distributions.\n\n"
        "Return STRICTLY a valid JSON object with keys 'agent' and 'tickers'. No explanation markdown blocks."
    )
    
    # Pack conversation context so the router remembers pronouns (e.g., "Is it safe?" referring to NVDA)
    conversation_context = state.get("messages", []) + [HumanMessage(content=state["query"])]
    
    try:
        response = llm.invoke([SystemMessage(content=system_prompt)] + conversation_context[-5:])
        raw_text = response.content.strip()
        
        if "```" in raw_text:
            raw_text = raw_text.split("```")[1]
            if raw_text.startswith("json"):
                raw_text = raw_text[4:]
        raw_text = raw_text.strip()
        
        routing_data = json.loads(raw_text)
        agent = routing_data.get("agent", "portfolio_health")
        tickers = routing_data.get("tickers", [])
    except Exception:
        agent = "portfolio_health"
        tickers = []
        
    return {"next_node": agent, "extracted_tickers": tickers}

def synthesizer_node(state: AgentState) -> Dict[str, Any]:
    api_key = os.getenv("GROQ_API_KEY")
    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.3, groq_api_key=api_key)
    
    agent_raw_data = state.get("agent_outputs", {})
    
    system_prompt = (
        "You are Valura AI's Client Communications Director. Synthesize the raw analytical data "
        "provided by specialized agents into a professional, clear, human-friendly wealth insight text response.\n\n"
        "Guidelines:\n"
        "- Be brief, conversational, yet authoritative.\n"
        "- Address the user's explicit query context directly.\n"
        "- Ensure any risk alerts (e.g., high concentration weights) or live market calculations are clearly spelled out.\n"
        "- Always append the dynamic agent compliance warning at the end gracefully."
    )
    
    user_input = f"User Query: {state['query']}\nRaw Agent Diagnostic Output: {json.dumps(agent_raw_data)}"
    response = llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=user_input)])
    
    return {"final_response": response.content.strip()}

def route_to_agent(state: AgentState) -> str:
    node = state.get("next_node", "portfolio_health")
    if node not in ["portfolio_health", "market_news", "tax_strategy"]:
        return "portfolio_health"
    return node

def compile_workflow():
    from src.agents.agent_network import portfolio_health_node, market_news_node, tax_strategy_node
    
    workflow = StateGraph(AgentState)
    
    workflow.add_node("router", router_node)
    workflow.add_node("portfolio_health", portfolio_health_node)
    workflow.add_node("market_news", market_news_node)
    workflow.add_node("tax_strategy", tax_strategy_node)
    workflow.add_node("synthesizer", synthesizer_node)
    
    workflow.set_entry_point("router")
    
    workflow.add_conditional_edges(
        "router",
        route_to_agent,
        {
            "portfolio_health": "portfolio_health",
            "market_news": "market_news",
            "tax_strategy": "tax_strategy"
        }
    )
    
    # Forward all computing nodes output straight to Synthesizer layer before ending
    workflow.add_edge("portfolio_health", "synthesizer")
    workflow.add_edge("market_news", "synthesizer")
    workflow.add_edge("tax_strategy", "synthesizer")
    
    workflow.add_edge("synthesizer", END)
    
    # Memory Saver Checkpointer layer directly into graph compilation matrix
    memory_store = MemorySaver()
    return workflow.compile(checkpointer=memory_store)