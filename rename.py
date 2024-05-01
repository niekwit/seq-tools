import csv
import os
from pathlib import Path

# Open the CSV file
with open('rename.csv', 'r') as file:
    reader = csv.reader(file)
    
    # Iterate over each row in the CSV file
    for row in reader:
        # Get the current and new file names from the row
        current_name = f"reads/{row[0]}"
        new_name = f"reads/{row[1]}"
        
        if "/" in row[1]:
            Path(os.path.dirname(new_name)).mkdir(parents=True, exist_ok=True)
        
        # Rename the file
        os.rename(current_name, new_name)
