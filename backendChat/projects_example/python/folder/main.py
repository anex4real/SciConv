import subprocess
import sys

# Install required packages if not already installed
def install_and_import(package, import_name=None):
    import_name = import_name or package
    try:
        __import__(import_name)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# Required external libraries
install_and_import("requests")
install_and_import("beautifulsoup4", "bs4")
install_and_import("matplotlib")

# Now safely import them
import requests
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
from collections import Counter

def main():
    # ✅ A real URL with rich content
    url = "https://en.wikipedia.org/wiki/Python_(programming_language)"
    try:
        response = requests.get(url)
        response.raise_for_status()
    except Exception as e:
        print("Failed to fetch the webpage:", e)
        return

    # Parse visible text from the page
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

    # ✅ Print results to the console
    print("\nTop 10 Most Common Words on the Wikipedia Page:")
    for word, count in top_words:
        print(f"{word}: {count}")

    # Plot results
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
