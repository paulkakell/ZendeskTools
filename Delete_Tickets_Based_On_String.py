import requests
import time
import base64
import configparser

# Load settings from INI file
config = configparser.ConfigParser()
config.read('zendesk_config.ini')

api_token = config.get('Zendesk', 'api_token')
auth_email = config.get('Zendesk', 'auth_email')
rate_limit = config.get('Zendesk', 'rate_limit')
specified_string = config.get('Zendesk', 'specified_string').lower()
subdomain = config.get('Zendesk', 'subdomain')

# Encode credentials for Basic Authentication
credentials = f"{auth_email}/api_token:{api_token}"
encoded_credentials = base64.b64encode(credentials.encode()).decode()

headers = {
    "Authorization": f"Basic {encoded_credentials}"
}

def search_tickets(page=1):
    """Search for closed tickets containing the specified string in the subject."""
    url = f"https://{subdomain}.zendesk.com/api/v2/search.json?query=type:ticket status:closed subject:*{specified_string}* page={page}"
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Failed to search tickets: {response.text}")
    return response.json()

def delete_ticket(ticket_id):
    """Delete a single ticket by its ID."""
    url = f"https://{subdomain}.zendesk.com/api/v2/tickets/{ticket_id}.json"
    response = requests.delete(url, headers=headers)
    if response.status_code != 204:
        raise Exception(f"Failed to delete ticket {ticket_id}: {response.text}")

def bulk_delete_tickets(ticket_ids):
    """Delete tickets in bulk while observing the rate limit."""
    for i, ticket_id in enumerate(ticket_ids, start=1):
        delete_ticket(ticket_id)
        if i % rate_limit == 0:
            print(f"Rate limit reached, sleeping for 60 seconds...")
            time.sleep(60)

def main():
    page = 1
    ticket_ids = []

    while True:
        results = search_tickets(page)
        tickets = results.get("results", [])
        if not tickets:
            break
        for ticket in tickets:
            subject = ticket["subject"].lower()
            if specified_string in subject:
                ticket_ids.append(ticket["id"])

        page += 1
        time.sleep(60 / rate_limit)  # Respect the rate limit

    print(f"Found {len(ticket_ids)} tickets to delete.")
    bulk_delete_tickets(ticket_ids)

if __name__ == "__main__":
    main()
