import requests

# 511 API Key (replace with your actual key or load from .env if you prefer)
API_KEY = "09ddeab2-9b3f-4531-8a35-5304443e02b4"

# Example map of station names to stop codes — you can add more
# STOP_CODES = {
#     "Fremont": "FRMT",
#     "Daly City": "DALY",
#     "Richmond": "RICH",
#     "Berryessa": "BERY"
# }


# Test the get_departures function works via a function call, like get_departures("UCTY"), then send it to me via Discord.
def get_departures(station_id):
    """
    Fetch upcoming departures for a given station using the 511 API.
    Args:
        station_name (str): User-friendly name like 'Fremont'
    Returns:
        str: List of upcoming trains formatted for display
    """
    # stop_id = STOP_CODES.get(station_name)

    # if not stop_id:
    #     return f"❌ Unknown station: {station_name}. Please try a different station."

    url = f"https://api.511.org/transit/StopMonitoring?api_key={API_KEY}&agency=BA&stopcode={station_id}"
    
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

            departures.append(f"🚋 {line_name} to {destination} - Arriving at: {arrival_time}")

        return "\n".join(departures)

    except Exception as e:
        return f"❌ Error contacting 511 API: {e}"

print(get_departures("16TH"))