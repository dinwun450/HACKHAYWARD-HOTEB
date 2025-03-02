import os
import streamlit as st
from groq import Groq
import transit_helper

# --- Directly set your Groq API key here ---
GROQ_API_KEY = "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"

# --- Other static chatbot setup ---
INITIAL_RESPONSE = "Hello! Ask me about public transit schedules and updates."
INITIAL_MSG = "Sure! Let me check the latest for you."
CHAT_CONTEXT = "You are a helpful assistant who answers questions about public transit using real-time data from Transit.land."

# Set Groq API key for the environment (Groq client needs this)
os.environ["GROQ_API_KEY"] = GROQ_API_KEY

# --- Streamlit page config ---
st.set_page_config(
    page_title="Transit Chatbot 🚌",
    page_icon="🚍",
    layout="centered",
)

# Initialize Groq client
client = Groq()

# Initialize chat history if not already set
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {"role": "assistant", "content": INITIAL_RESPONSE},
    ]

# --- Page Header ---
st.title("Transit Chatbot 🚌")
st.caption("Ask me about transit times, departures, and station info!")

# --- Display chat history ---
for message in st.session_state.chat_history:
    with st.chat_message(message["role"], avatar="🤖" if message["role"] == "assistant" else "🗨️"):
        st.markdown(message["content"])

# --- User input field ---
user_prompt = st.chat_input("Ask me about transit...")

def parse_groq_stream(stream):
    """Helper to extract streamed content from Groq API response."""
    content = ""
    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content is not None:
            content += chunk.choices[0].delta.content
            yield chunk.choices[0].delta.content
    return content

# --- If user submits a question ---
if user_prompt:
    # Display user message immediately
    with st.chat_message("user", avatar="🗨️"):
        st.markdown(user_prompt)

    # Add user message to chat history
    st.session_state.chat_history.append({"role": "user", "content": user_prompt})

    # Create full message history (including system and initial assistant messages)
    messages = [
        {"role": "system", "content": CHAT_CONTEXT},
        {"role": "assistant", "content": INITIAL_MSG},
        *st.session_state.chat_history
    ]

    # Ask Groq for a response and stream it to the user
    with st.chat_message("assistant", avatar="🤖"):
        stream = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
            stream=True
        )
        response = st.write_stream(parse_groq_stream(stream))

    # Very simple logic to extract stop name (last two words, can be improved later)
    stop_name = response.split()[-2] + " " + response.split()[-1]
    st.markdown(f"📍 **Detected stop:** {stop_name}")

    # Fetch live departures from Transit.land
    departures = transit_helper.get_departures(stop_name)

    # Show the departures to the user
    st.markdown(f"🚌 **{departures}**")

    # Add the assistant's full message (Groq response + departures) to the chat history
    st.session_state.chat_history.append({
        "role": "assistant",
        "content": f"{response}\n\n{departures}"
    })
 