import os
import requests
import json
import streamlit as st
from groq import Groq
from dotenv import dotenv_values


def get_all_transit_operators():
    all_operators = {}
    url = f"http://api.511.org/transit/gtfsoperators?api_key=09ddeab2-9b3f-4531-8a35-5304443e02b4"
    response = requests.get(url)
    response.encoding = 'utf-8-sig'

    if response.status_code != 200:
        return None
    else:
        the_operators = response.json()
        for operator in the_operators:
            all_operators[operator['Name']] = operator['Id']
        
        return all_operators

# replace url with service alerts (api call function)
def caller_on_transit_lines(operator_id):
    all_of_the_lines = []
    the_operators = get_all_transit_operators()

    if the_operators[operator_id] is not None:
        operator_id = the_operators[operator_id]
        url = f"https://api.511.org/transit/servicealerts?api_key=09ddeab2-9b3f-4531-8a35-5304443e02b4&agency={operator_id}&format=JSON"
        response = requests.get(url)
        response.encoding = 'utf-8-sig'

        if response.status_code != 200:
            return None
        else:
            all_lines = response.json()
            for line in all_lines["Entities"]:
                all_of_the_lines.append(f"{line['Alert']['HeaderText']['Translations'][0]['Text']} : {line['Alert']['DescriptionText']['Translations'][0]['Text']}")
            
            return all_of_the_lines
print(caller_on_transit_lines("AC TRANSIT"))

def get_transit_lines_from_operator(operator_id):
    return caller_on_transit_lines(operator_id)

client = Groq(api_key="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")
MODEL = 'llama3-70b-8192'

def run_conversation(user_prompt):
    messages=[
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
        }
    ]

    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=tools,
        tool_choice="auto",
        max_tokens=4096
    )

    response_message = response.choices[0].message
    tool_calls = response_message.tool_calls

    if tool_calls:
        # Step 3: call the function
        # Note: the JSON response may not always be valid; be sure to handle errors
        available_functions = {
            "get_transit_lines_from_operator": get_transit_lines_from_operator
        }  # only one function in this example, but you can have multiple
        messages.append(response_message)  # extend conversation with assistant's reply
        # Step 4: send the info for each function call and function response to the model
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_to_call = available_functions[function_name]
            function_args = json.loads(tool_call.function.arguments)
            function_response = function_to_call(
                operator_id=function_args.get("operator_id")
            )
            messages.append(
                {
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": " ".join(function_response) if function_response else "No results found",
                }
            )  # extend conversation with function response

        print(messages)

        second_response = client.chat.completions.create(
            model=MODEL,
            messages=messages
        )  # get a new response from the model where it can see the function response
        return second_response.choices[0].message.content
    
# Streamlit interface setup
st.title("Transit Line Information Chatbot")
st.caption("Ask about the transit lines for specific operators.")

# Display chat history (if any)
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Show the conversation so far
for message in st.session_state.chat_history:
    with st.chat_message(message["role"], avatar="🤖" if message["role"] == "assistant" else "🗨️"):
        st.markdown(message["content"])

# User input field
user_input = st.chat_input("Ask a question...")

if user_input:
    # Display user message
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    
    # Call Groq to process the prompt
    assistant_response = run_conversation(user_input)

    # Display assistant's response
    st.session_state.chat_history.append({"role": "assistant", "content": assistant_response})

    # Update chat interface
    st.rerun()

