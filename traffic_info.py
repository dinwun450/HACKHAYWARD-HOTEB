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

        for incident in all_of_the_lines:
            print(incident)
        return all_of_the_lines

def get_traffic_data():
    return caller()
