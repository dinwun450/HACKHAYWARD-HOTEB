import os
import streamlit as st
from groq import Groq
# import transit_helper
from groqify import get_departures, get_traffic_alerts, get_transit_alerts_from_operator, get_transit_lines_from_operator, get_all_transit_operators, MODEL
import json

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

messages = [
    {
        "role": "system",
        "content": "You are a function calling LLM that uses the data extracted from the function and responds to "
                    "the user with the result of the function."
    },
    {
        "role": "user",
        "content": user_prompt,
    }
]

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_transit_lines_from_operator",
            "description": "Get all transit lines from a specific transit operator",
            "parameters": {
                "type": "object",
                "properties": {
                    "operator_id": {
                        "type": "string",
                        "description": "The name of the transit operator, in two-letter code format",
                    }
                },
                "required": ["operator_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_departures",
            "description": "Get upcoming departures from a specific station",
            "parameters": {
                "type": "object",
                "properties": {
                    "operator_id": {
                        "type": "string",
                        "description": "The name of the transit operator, in two-letter code format",
                    },
                    "station_id": {
                        "type": "string",
                        "description": "The station ID of the station to get departures from",
                    }
                },
                "required": ["operator_id", "station_id"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_transit_alerts_from_operator",
            "description": "Get all transit alerts from a specific transit operator",
            "parameters": {
                "type": "object",
                "properties": {
                    "operator_id": {
                        "type": "string",
                        "description": "The name of the transit operator, in two-letter code format",
                    }
                },
                "required": ["operator_id"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_traffic_alerts",
            "description": "Get all traffic alerts that are active.",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        }
    }
]

# --- If user submits a question ---
if user_prompt:
    # Display user message immediately
    with st.chat_message("user", avatar="🗨️"):
        st.markdown(user_prompt)

    # Add user message to chat history
    st.session_state.chat_history.append({"role": "user", "content": user_prompt})

    # Create full message history (including system and initial assistant messages)
    # messages = [
    #     {"role": "system", "content": CHAT_CONTEXT},
    #     {"role": "assistant", "content": INITIAL_MSG},
    #     *st.session_state.chat_history
    # ]

    # Ask Groq for a response and stream it to the user
    with st.chat_message("assistant", avatar="🤖"):
        stream = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            max_tokens=4096
        )
        response_message = stream.choices[0].message
        tool_calls = response_message.tool_calls

        if tool_calls:
            # Step 3: call the function
            # Note: the JSON response may not always be valid; be sure to handle errors
            available_functions = {
                "get_transit_lines_from_operator": get_transit_lines_from_operator,
                "get_departures": get_departures,
                "get_traffic_alerts": get_traffic_alerts,
                "get_transit_alerts_from_operator": get_transit_alerts_from_operator,
            }
            messages.append(response_message)  # extend conversation with assistant's reply

            # Step 4: send the info for each function call and function response to the model
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_to_call = available_functions[function_name]
                function_args = json.loads(tool_call.function.arguments)

                if function_to_call == get_departures:
                    function_response = function_to_call(
                        operator_id=function_args.get("operator_id"),
                        station_id=function_args.get("station_id")
                    )
                elif function_to_call == get_traffic_alerts:
                    function_response = function_to_call()
                else:
                    function_response = function_to_call(
                        operator_id=function_args.get("operator_id")
                    )

                messages.append(
                    {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": "\n".join(function_response) if function_response else "No results found",
                    }
                )  # extend conversation with function response

            second_response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                stream=True
            )
            result = st.write_stream(parse_groq_stream(second_response))

    # Very simple logic to extract stop name (last two words, can be improved later)
    # stop_name = response.split()[-2] + " " + response.split()[-1]
    # st.markdown(f"📍 **Detected stop:** {stop_name}")

    # Fetch live departures from Transit.land
    # departures = transit_helper.get_departures(stop_name)

    # Show the departures to the user
    # st.markdown(f"🚌 **{departures}**")

    # Add the assistant's full message (Groq response + departures) to the chat history
    st.session_state.chat_history.append({
        "role": "assistant",
        "content": f"{result}"
    })
 
