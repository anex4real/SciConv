#!/bin/bash

# Step 1: Ensure pip is available
if ! command -v pip &> /dev/null; then
    echo "pip is not installed. Please install pip and try again."
    exit 1
fi

# Step 2: Install required Python packages
pip install --quiet requests beautifulsoup4 matplotlib

# Step 3: Run the Python code
python3 <<EOF
import requests
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
from collections import Counter

def main():
    url = "https://en.wikipedia.org/wiki/Python_(programming_language)"
    try:
        response = requests.get(url)
        response.raise_for_status()
    except Exception as e:
        print("Failed to fetch the webpage:", e)
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    for script_or_style in soup(["script", "style"]):
        script_or_style.decompose()
    text = soup.get_text().lower()
    words = [word for word in text.split() if word.isalpha()]
    counter = Counter(words)
    top_words = counter.most_common(10)

    if not top_words:
        print("No words found on the page.")
        return

    print("\nTop 10 Most Common Words on the Wikipedia Page:")
    for word, count in top_words:
        print(f"{word}: {count}")

    labels, values = zip(*top_words)
    plt.figure(figsize=(10, 6))
    plt.bar(labels, values)
    plt.title("Top 10 Most Common Words on Wikipedia - Python (Programming Language)")
    plt.xlabel("Words")
    plt.ylabel("Frequency")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()
EOF

#chmod +x file.sh && ./file.sh
