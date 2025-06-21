import requests
from dotenv import load_dotenv

# Just to satisfy the use of dotenv — call it even though there's no .env
load_dotenv()

# Make a simple GET request using `requests`
response = requests.get("https://httpbin.org/ip")

# Print the response
print("Your IP is:", response.json().get("origin"))
