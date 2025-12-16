# example.py
# Uses 3 dependencies: pandas, numpy, and tabulate
# Prints a simple result directly to the console

import pandas as pd
import numpy as np
from tabulate import tabulate

# Data stored locally (no web requests)
data = [
    {"id": 1, "name": "Alice", "age": 25},
    {"id": 2, "name": "Bob", "age": 30},
    {"id": 3, "name": "Charlie", "age": 22},
]

# Create DataFrame
df = pd.DataFrame(data)

# Add a computed column using numpy
df["score"] = np.random.randint(60, 100, size=len(df))

# Print a simple text result — not a UI table
for _, row in df.iterrows():
    print(f"ID: {row['id']}, Name: {row['name']}, Age: {row['age']}, Score: {row['score']}")
