import os
import json
import glob
import networkx as nx
from collections import defaultdict

DATA_DIR = r"c:\Users\gsath\OneDrive\Desktop\p\Dodge_AI_Dataset\sap-o2c-data"

def load_jsonl(subdir):
    path = os.path.join(DATA_DIR, subdir, "*.jsonl")
    records = []
    for file_path in glob.glob(path):
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    records.append(json.loads(line))
    return records

def build_graph():
    G = nx.DiGraph()

    # 1. Customers and Sales Orders
    so_headers = load_jsonl("sales_order_headers")
    for so in so_headers:
        so_id = so["salesOrder"]
        customer_id = so.get("soldToParty")
        
        G.add_node(f"SO_{so_id}", type="SalesOrder", **so)
        if customer_id:
            G.add_node(f"CUST_{customer_id}", type="Customer", id=customer_id)
            G.add_edge(f"CUST_{customer_id}", f"SO_{so_id}", relation="PLACED")

    # Sales Order Items 
    so_items = load_jsonl("sales_order_items")
    for item in so_items:
        so_id = item["salesOrder"]
        item_id = item["salesOrderItem"]
        node_id = f"SOItem_{so_id}_{item_id}"
        G.add_node(node_id, type="SalesOrderItem", **item)
        G.add_edge(f"SO_{so_id}", node_id, relation="HAS_ITEM")
        
        # Product link
        material = item.get("material")
        if material:
            G.add_node(f"PROD_{material}", type="Product", id=material)
            G.add_edge(node_id, f"PROD_{material}", relation="IS_PRODUCT")

    # 2. Outbound Deliveries
    del_headers = load_jsonl("outbound_delivery_headers")
    for d in del_headers:
        del_id = d["deliveryDocument"]
        G.add_node(f"DEL_{del_id}", type="Delivery", **d)

    del_items = load_jsonl("outbound_delivery_items")
    for d_item in del_items:
        del_id = d_item["deliveryDocument"]
        d_item_id = d_item["deliveryDocumentItem"]
        ref_so = d_item.get("referenceSdDocument")
        ref_so_item = d_item.get("referenceSdDocumentItem")
        
        node_id = f"DELItem_{del_id}_{d_item_id}"
        G.add_node(node_id, type="DeliveryItem", **d_item)
        G.add_edge(f"DEL_{del_id}", node_id, relation="HAS_ITEM")
        
        if ref_so:
            # Link Delivery to Sales Order at Header Level
            G.add_edge(f"SO_{ref_so}", f"DEL_{del_id}", relation="DELIVERED_BY")
            # Link Item level
            if ref_so_item:
                G.add_edge(f"SOItem_{ref_so}_{ref_so_item}", node_id, relation="FULFILLED_BY")
                
        plant = d_item.get("plant")
        if plant:
            G.add_node(f"PLANT_{plant}", type="Plant", id=plant)
            G.add_edge(node_id, f"PLANT_{plant}", relation="FROM_PLANT")

    # 3. Billing Documents
    bill_headers = load_jsonl("billing_document_headers")
    for b in bill_headers:
        bill_id = b["billingDocument"]
        G.add_node(f"BILL_{bill_id}", type="BillingDocument", **b)

    bill_items = load_jsonl("billing_document_items")
    for b_item in bill_items:
        bill_id = b_item["billingDocument"]
        b_item_id = b_item["billingDocumentItem"]
        ref_del = b_item.get("referenceSdDocument")
        ref_del_item = b_item.get("referenceSdDocumentItem")
        
        node_id = f"BILLItem_{bill_id}_{b_item_id}"
        G.add_node(node_id, type="BillingItem", **b_item)
        G.add_edge(f"BILL_{bill_id}", node_id, relation="HAS_ITEM")
        
        if ref_del:
            # Link Delivery to Billing
            G.add_edge(f"DEL_{ref_del}", f"BILL_{bill_id}", relation="BILLED_BY")
            if ref_del_item:
                 G.add_edge(f"DELItem_{ref_del}_{ref_del_item}", node_id, relation="BILLED_BY")

        material = b_item.get("material")
        if material:
            G.add_node(f"PROD_{material}", type="Product", id=material)
            G.add_edge(node_id, f"PROD_{material}", relation="IS_PRODUCT")

    # 4. Journal Entries
    je_items = load_jsonl("journal_entry_items_accounts_receivable")
    for je in je_items:
        je_id = je["accountingDocument"]
        ref_bill = je.get("referenceDocument")
        
        je_node = f"JE_{je_id}"
        G.add_node(je_node, type="JournalEntry", **je)
        
        if ref_bill:
            G.add_edge(f"BILL_{ref_bill}", je_node, relation="RECORDED_IN")

    return G

if __name__ == "__main__":
    g = build_graph()
    print(f"Graph built successfully! Nodes: {g.number_of_nodes()}, Edges: {g.number_of_edges()}")
