import requests
import json
from groq import Groq
import py_oldict

def get_all_transit_operators():
    print("Get em!")
    return py_oldict.all_of_em

def caller_on_transit_lines(operator_id):
    all_of_the_lines = []
    the_operators = get_all_transit_operators()

    if the_operators[operator_id] is not None:
        operator_id = the_operators[operator_id]
        url = f"http://api.511.org/transit/lines?api_key=[API_KEY]&operator_id={operator_id}"
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

    url = f"https://api.511.org/transit/StopMonitoring?api_key=[API_KEY]&agency={the_operators[operator_id]}&stopcode={station_id}"
    
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
        url = f"https://api.511.org/transit/servicealerts?api_key=[API_KEY]&agency={operator_id}&format=JSON"
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
    url = f"http://api.511.org/traffic/events?api_key=[API_KEY]"
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

MODEL = 'llama3-70b-8192'
