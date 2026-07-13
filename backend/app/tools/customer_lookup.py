import json
from pathlib import Path


def get_customer_details(email: str):
    """
    Simulates Salesforce customer lookup using sample data.
    Reads customer records from data/customers.json.
    """

    file_path = Path("data/demo/customers.json")

    if not file_path.exists():
        return {
            "name": "Unknown Customer",
            "plan": "Unknown",
            "status": "data_file_missing",
            "company": "Unknown",
            "priority": "low"
        }

    with open(file_path, "r") as file:
        customers = json.load(file)

    return customers.get(email, {
        "name": "Unknown Customer",
        "plan": "Unknown",
        "status": "not_found",
        "company": "Unknown",
        "priority": "low"
    })
