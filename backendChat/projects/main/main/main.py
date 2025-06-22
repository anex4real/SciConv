import requests
import pandas as pd

def fetch_data(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

def main():
    url = "https://jsonplaceholder.typicode.com/users"
    data = fetch_data(url)
    
    if data:
        df = pd.DataFrame(data)
        print("Data retrieved successfully:\n")
        print(df[['id', 'name', 'email']])
    else:
        print("No data to display.")

if __name__ == "__main__":
    main()
