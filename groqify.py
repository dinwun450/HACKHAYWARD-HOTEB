import requests
import json
from groq import Groq

def get_all_transit_operators():
    the_operators = open("HackHaywardHackathon/the_bigoldict.json", "r")
    the_operators = json.load(the_operators)
    return the_operators

def caller_on_transit_lines(operator_id):
    all_of_the_lines = []
    the_operators = get_all_transit_operators()
    print(the_operators)

    if the_operators[operator_id] is not None:
        operator_id = the_operators[operator_id]
        url = f"http://api.511.org/transit/lines?api_key=09ddeab2-9b3f-4531-8a35-5304443e02b4&operator_id={operator_id}"
        response = requests.get(url)
        response.encoding = 'utf-8-sig'

        if response.status_code != 200:
            return None
        else:
            all_lines = response.json()
            for line in all_lines:
                all_of_the_lines.append(f"{line['PublicCode']} - {line['Name']}")
            
            return all_of_the_lines

def get_transit_lines_from_operator(operator_id):
    return caller_on_transit_lines(operator_id)

def get_departures(operator_id, station_id):
    the_operators = get_all_transit_operators()
    """
    Fetch upcoming departures for a given station using the 511 API.
    Args:
        station_id (str): User-friendly name like 'FRMT'
    Returns:
        str: List of upcoming trains formatted for display
    """
    # stop_id = STOP_CODES.get(station_name)

    # if not stop_id:
    #     return f"❌ Unknown station: {station_name}. Please try a different station."

    if the_operators[operator_id] is None:
        return f"❌ Unknown operator: {operator_id}. Please try a different operator."

    url = f"https://api.511.org/transit/StopMonitoring?api_key=09ddeab2-9b3f-4531-8a35-5304443e02b4&agency={the_operators[operator_id]}&stopcode={station_id}"
    
    try:
        response = requests.get(url)
        response.encoding = 'utf-8-sig'
        
        if response.status_code != 200:
            return f"❌ Failed to fetch data for {station_id}. Status: {response.status_code}"

        data = response.json()

        # Extract the relevant list of visits
        visits = data.get("ServiceDelivery", {}).get("StopMonitoringDelivery", {}).get("MonitoredStopVisit", [])

        if not visits:
            return f"No upcoming departures found for **{station_id}**."

        # Format upcoming departures into a list
        departures = []
        for visit in visits[:5]:  # Show up to 5 departures
            journey = visit.get("MonitoredVehicleJourney", {})
            line_name = journey.get("PublishedLineName", "Unknown Line")
            destination = journey.get("DestinationName", "Unknown Destination")
            arrival_time = journey.get("MonitoredCall", {}).get("ExpectedArrivalTime", "Unknown Time")

            departures.append(f"{line_name} to {destination} - Arriving at: {arrival_time}")

        return departures

    except Exception as e:
        return f"❌ Error contacting 511 API: {e}"

# replace url with service alerts (api call function)
def caller_on_transit_alerts(operator_id):
    all_of_the_alerts = []
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
                all_of_the_alerts.append(f"{line['Alert']['HeaderText']['Translations'][0]['Text']} : {line['Alert']['DescriptionText']['Translations'][0]['Text']}")
            
            return all_of_the_alerts

def get_transit_alerts_from_operator(operator_id):
    return caller_on_transit_alerts(operator_id)

def caller():
    all_of_the_lines = []
    url = f"http://api.511.org/traffic/events?api_key=09ddeab2-9b3f-4531-8a35-5304443e02b4"
    response = requests.get(url)
    response.encoding = 'utf-8-sig'

    if response.status_code != 200:
        return None
    else:
        all_lines = response.json()
        for line in all_lines["events"]:
            # Example: append relevant event information
            all_of_the_lines.append(f"Event: {line['headline']}")
        return all_of_the_lines

def get_traffic_alerts():
    return caller()

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
                    "content": " ".join(function_response) if function_response else "No results found",
                }
            )  # extend conversation with function response

        second_response = client.chat.completions.create(
            model=MODEL,
            messages=messages
        )  # get a new response from the model where it can see the function response
        return second_response.choices[0].message.content
    
prompt = input("Enter a prompt: ")
print(run_conversation(prompt))