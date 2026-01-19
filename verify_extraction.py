
import config
from extract_table import extract_transactions_from_pdf, clean_and_format_dataframe
import pandas as pd

def verify():
    pdf_path = "relevé.pdf"
    print(f"Extracting from {pdf_path}...")
    df = extract_transactions_from_pdf(pdf_path)
    df = clean_and_format_dataframe(df)
    
    # Filter for the problematic amount
    # Check credit or debit containing 979
    # Convert to string to search
    
    for i, row in df.iterrows():
        c = row.get('credit', 0.0)
        # Check tolerance or string match
        if 970000 < c < 30000000: # Range check: 979k or 29M
            print(f"MATCH Row {i}: Credit={c}")
            print(f"Libelle: {row.get('libelle')}")

if __name__ == "__main__":
    verify()
