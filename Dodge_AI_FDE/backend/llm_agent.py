import os
import networkx as nx
from typing import List, Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field
from langchain_core.tools import tool

# Global reference to graph
_graph = None

def set_graph(g: nx.DiGraph):
    global _graph
    _graph = g

@tool
def get_top_products_by_billing(limit: int = 5) -> str:
    """Finds the products associated with the highest number of billing documents. Useful for queries about product billing frequency."""
    if not _graph: return "Graph not loaded."
    product_counts = {}
    for u, v, data in _graph.edges(data=True):
        if data.get("relation") == "IS_PRODUCT":
            # u is usually the item (BillingItem, SalesOrderItem), v is Product
            if _graph.nodes[u].get("type") == "BillingItem":
                product_counts[v] = product_counts.get(v, 0) + 1
                
    sorted_prods = sorted(product_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
    result = []
    for prod_node, count in sorted_prods:
        prod_id = _graph.nodes[prod_node].get("id", prod_node)
        result.append(f"Product {prod_id} appears in {count} billing items.")
    return "\n".join(result) if result else "No product billing data found."

@tool
def trace_flow(document_id: str) -> str:
    """Traces the full O2C flow for a given document (e.g. a billing document or sales order). Pass just the ID. Useful for tracing or tracking flows."""
    if not _graph: return "Graph not loaded."
    
    # Locate the node. It could be SO_..., DEL_..., BILL_...
    start_node = None
    for n in _graph.nodes:
        if document_id in str(n) and "Item" not in str(n):
            start_node = n
            break
            
    if not start_node:
        return f"Document {document_id} not found."
    
    # We want to find the connected component or traverse up/down.
    # Since it's a directed graph linking SO->DEL->BILL->JE, we can use an undirected version to find the whole flow.
    undirected_G = _graph.to_undirected()
    flow_nodes = nx.node_connected_component(undirected_G, start_node)
    
    # Filter to only the core document headers to keep it clean
    headers = [n for n in flow_nodes if _graph.nodes[n].get("type") in ["SalesOrder", "Delivery", "BillingDocument", "JournalEntry"]]
    
    # Sort them by natural flow: SO -> DEL -> BILL -> JE
    order = {"SalesOrder": 1, "Delivery": 2, "BillingDocument": 3, "JournalEntry": 4}
    try:
        sorted_flow = sorted(headers, key=lambda n: order.get(_graph.nodes[n].get("type"), 99))
    except Exception:
        sorted_flow = headers
        
    res = [f"Found Flow for {document_id}:"]
    for node in sorted_flow:
        node_type = _graph.nodes[node].get("type")
        n_id = _graph.nodes[node].get("salesOrder") or _graph.nodes[node].get("deliveryDocument") or _graph.nodes[node].get("billingDocument") or _graph.nodes[node].get("accountingDocument") or node
        res.append(f"- {node_type}: {n_id}")
    return "\n".join(res)

@tool
def get_broken_flows() -> str:
    """Identify flow anomalies, such as sales orders that have a delivery but no billing, or are delivered but incomplete. Useful for finding broken flows."""
    if not _graph: return "Graph not loaded."
    
    broken = []
    # A simple definition of broken: 
    # Sales Order -> Delivery -> no Billing
    for n, data in _graph.nodes(data=True):
        if data.get("type") == "SalesOrder":
            # find deliveries
            deliveries = [v for u, v, edata in _graph.out_edges(n, data=True) if edata.get("relation") == "DELIVERED_BY"]
            for del_node in deliveries:
                # check if delivery has billing
                billings = [v for u, v, edata in _graph.out_edges(del_node, data=True) if edata.get("relation") == "BILLED_BY"]
                if not billings:
                    so_id = data.get("salesOrder")
                    del_id = _graph.nodes[del_node].get("deliveryDocument")
                    broken.append(f"Sales Order {so_id} has Delivery {del_id} but NO Billing Document.")
                    if len(broken) >= 10:
                        break # Limit output
        if len(broken) >= 10:
            break
            
    return "\n".join(broken) if broken else "No broken flows detected."

def get_agent():
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        print("WARNING: GEMINI_API_KEY not set.")
        
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash", 
        google_api_key=api_key,
        temperature=0
    )
    tools = [get_top_products_by_billing, trace_flow, get_broken_flows]
    llm_with_tools = llm.bind_tools(tools)
    return llm_with_tools

from langchain_core.messages import SystemMessage, HumanMessage

SYSTEM_PROMPT = """You are Dodge AI, an intelligent agent built for a graph-based Order-to-Cash (O2C) system.
You help users explore SAP data relating to Sales Orders, Deliveries, Billing, and Journal Entries.
You MUST ONLY answer questions related to the provided dataset and domain.
If the user asks something unrelated (e.g. creative writing, general knowledge, or completely off-topic questions), you must politely reject it by saying:
"This system is designed to answer questions related to the provided dataset only."
Always use the provided tools to query the graph data when the user asks analytical questions, like "highest billing products", "trace the flow", or "broken flows".
Do not guess the data. Use the tools.
"""

def chat(query: str, chat_history: List[Any] = None) -> str:
    agent = get_agent()
    messages = [SystemMessage(content=SYSTEM_PROMPT)]
    if chat_history:
        messages.extend(chat_history)
    messages.append(HumanMessage(content=query))
    
    # Step 1: LLM decides to use tool or directly answer
    res = agent.invoke(messages)
    
    if res.tool_calls:
        # Step 2: Execute tool and return to LLM
        messages.append(res)
        tool_map = {t.name: t for t in [get_top_products_by_billing, trace_flow, get_broken_flows]}
        for tool_call in res.tool_calls:
            tool_fn = tool_map[tool_call["name"]]
            tool_output = tool_fn.invoke(tool_call["args"])
            from langchain_core.messages import ToolMessage
            messages.append(ToolMessage(content=str(tool_output), tool_call_id=tool_call["id"]))
        final_res = agent.invoke(messages)
        return final_res.content
    else:
        return res.content
