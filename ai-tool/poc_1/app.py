import streamlit as st
from groq import Groq
import json
import os


# ===== REPLACE WITH YOUR GROQ API KEY =====
GROQ_API_KEY = "YOUR_GROQ_API_KEY"
# Optional: allow selecting model via environment variable so you can
# switch away from decommissioned models without changing code.
# Default to qwen/qwen3-32b unless the env var overrides it.
GROQ_MODEL = os.environ.get("GROQ_MODEL", "qwen/qwen3-32b")
# ==========================================


# Page configuration
st.set_page_config(
    page_title="Sales Order Assistant",
    page_icon="document",
    layout="wide"
)


# Initialize Groq client
@st.cache_resource
def get_groq_client():
    return Groq(api_key=GROQ_API_KEY)


try:
    client = get_groq_client()
except Exception as e:
    st.error(f"Error initializing Groq client: {str(e)}")
    st.stop()


# Load data from JSON file
@st.cache_data
def load_sales_order_data():
    """Load sales order data from data.json"""
    try:
        with open("data.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("data.json file not found!")
        return None
    except json.JSONDecodeError:
        st.error("Error parsing data.json!")
        return None


# Load data
sales_data = load_sales_order_data()


if sales_data is None:
    st.stop()


def get_invoice_details():
    """Returns invoice and purchase order details"""
    return {
        "invoice_number": sales_data["invoice_number"],
        "purchase_order_number": sales_data["purchase_order_number"],
        "purchase_order_creation_date": sales_data["purchase_order_creation_date"],
        "contract_person_name": sales_data["contract_person_name"],
        "invoice_amount": sales_data["invoice_amount"],
        "currency": sales_data["currency"]
    }


def get_customer_details():
    """Returns customer name and bill to address"""
    return {
        "customer_name": sales_data["customer_name"],
        "bill_to_address": sales_data["bill_to_address"]
    }


def get_ship_to_address():
    """Returns ship to address details"""
    return {
        "ship_to_address": sales_data["ship_to_address"]
    }


def get_sales_order_details():
    """Returns sales order number and contracting parties"""
    return {
        "sales_order_number": sales_data["sales_order_number"],
        "contracting_parties": sales_data["contracting_parties"]
    }


def get_work_order_details():
    """Returns work order dates and authorized signatory"""
    return {
        "work_order_start_date": sales_data["work_order_start_date"],
        "work_order_end_date": sales_data["work_order_end_date"],
        "authorized_signatory": sales_data["authorized_signatory"]
    }


def get_key_deliverables():
    """Returns list of key deliverables"""
    return {
        "sales_order_number": sales_data["sales_order_number"],
        "key_deliverables": sales_data["key_deliverables"]
    }


def get_relevant_data(user_query):
    """Map user query to appropriate data function"""
    query_lower = user_query.lower()
    
    if any(keyword in query_lower for keyword in ["invoice", "purchase order", "po number", "contract person", "po", "po creation"]):
        return get_invoice_details()
    elif any(keyword in query_lower for keyword in ["customer name", "bill to", "billing address", "customer", "bill"]):
        return get_customer_details()
    elif any(keyword in query_lower for keyword in ["ship to", "shipping address", "delivery address", "ship", "delivery"]):
        return get_ship_to_address()
    elif any(keyword in query_lower for keyword in ["sales order", "contracting parties", "vendor", "parties", "so"]):
        return get_sales_order_details()
    elif any(keyword in query_lower for keyword in ["work order", "start date", "end date", "signatory", "authorized", "wo"]):
        return get_work_order_details()
    elif any(keyword in query_lower for keyword in ["deliverable", "key deliverable", "milestones", "deliverables"]):
        return get_key_deliverables()
    else:
        return None


def generate_response(user_query, relevant_data):
    """Generate natural language response using Groq LLM with JSON data"""
    
    system_prompt = """You are a professional sales order assistant with strict output rules.
You HAVE ACCESS to sales order data in JSON format.

Output rules (MUST follow):
1) Never reveal or output internal chain-of-thought, reasoning steps, or any `<think>` or similar sections. Do NOT output any hidden reasoning or analysis.
2) Only return the requested answer. Do NOT add extra commentary, explanations, or diagnostics.
3) Format the answer exactly as plain text lines with a label, a colon, a space, then the value. For example:
   Invoice Number: INV-2025-001234
   Purchase Order Number: PO-2025-789456
   Purchase Order Creation Date: 2025-10-15
   Contract Person Name: Rajesh Kumar
   Invoice Amount: ₹1,250,000.00
   Currency: INR (Indian Rupee)
4) If the user requested specific fields, only include those fields in the response (no extra fields).
5) Use the provided JSON data to fill values and format numeric currency values with two decimals and thousands separators when applicable.

Follow these rules exactly and only output the plain answer lines requested by the user."""
    
    user_prompt = f"""User Question: {user_query}

Relevant Data (JSON):
{json.dumps(relevant_data, indent=2)}

Please provide a clear, well-formatted answer to the user's question based on the above data."""
    
    try:
        # Allow overriding the model via GROQ_MODEL env var. If it's not set,
        # the SDK will attempt to use the default model we passed here.
        model_to_use = GROQ_MODEL or "llama-3.1-70b-versatile"

        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model=model_to_use,
            temperature=0.3,
            max_tokens=1024,
        )

        return chat_completion.choices[0].message.content
    except Exception as e:
        err_text = str(e)
        # Detect a common decommission error and provide actionable guidance
        if "decommissioned" in err_text or "model_decommissioned" in err_text:
            return (
                "Error generating response: the model you requested appears to be decommissioned.\n"
                "Details: "
                f"{err_text}\n\n"
                "Fix: set the environment variable `GROQ_MODEL` to a currently supported model name and restart the app. "
                "See https://console.groq.com/docs/deprecations for recommended replacements."
            )

        return f"Error generating response: {err_text}"


# ============== STREAMLIT UI ==============

st.title("Sales Order Assistant")
st.markdown("An intelligent assistant for querying sales orders, invoices, and related business documents")
st.markdown("---")


# Sidebar with predefined questions
st.sidebar.title("Quick Questions")
st.sidebar.markdown("Click any button below to ask a pre-defined question:")


predefined_questions = [
    "Show me the Invoice number, Purchase order number, Purchase order creation date, contract person name and invoice amount along with currency detail",
    "Show me the customer name and bill to address",
    "Show me the ship to address detail",
    "Show me the sales order number and the contracting parties detail",
    "Show me the work order start and end date along with authorized signatory detail",
    "Provide me the list of key deliverables in the sales order"
]


# Initialize session state for messages
if "messages" not in st.session_state:
    st.session_state.messages = []


# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("json_data"):
            with st.expander("View Raw JSON Data"):
                st.json(message["json_data"])


# Sidebar buttons for predefined questions
st.sidebar.markdown("---")
for i, question in enumerate(predefined_questions):
    if st.sidebar.button(f"Q{i+1}: {question[:45]}...", key=f"btn_{i}", use_container_width=True):
        st.session_state.selected_question = question


# Handle selected question from sidebar
if "selected_question" in st.session_state:
    user_query = st.session_state.selected_question
    del st.session_state.selected_question
    
    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": user_query})
    
    # Get relevant data
    relevant_data = get_relevant_data(user_query)
    
    if relevant_data:
        # Generate response using Groq
        response = generate_response(user_query, relevant_data)
        
        # Add assistant message with JSON data
        st.session_state.messages.append({
            "role": "assistant",
            "content": response,
            "json_data": relevant_data
        })
    else:
        st.session_state.messages.append({
            "role": "assistant",
            "content": "I could not find relevant information for that query. Please try asking about invoices, purchase orders, customer details, shipping address, sales orders, work orders, or deliverables."
        })
    
    st.rerun()


# Free-text chat input removed per configuration — use the predefined questions in the sidebar
st.info("This app uses only the predefined Quick Questions in the sidebar. The free-text chat input has been disabled.")


# Add clear chat button in sidebar
st.sidebar.markdown("---")
if st.sidebar.button("Clear Chat History", use_container_width=True):
    st.session_state.messages = []
    st.rerun()


# Display info in sidebar
st.sidebar.markdown("---")
st.sidebar.markdown("### About")
st.sidebar.info("""
This assistant can answer questions about:
- Invoice and Purchase Order details
- Customer and Billing information
- Shipping address
- Sales order and contracting parties
- Work order dates and signatories
- Key deliverables and milestones
""")


# Display current data source
st.sidebar.markdown("---")
st.sidebar.markdown("### Data Source")
st.sidebar.caption("Loading data from: data.json")
