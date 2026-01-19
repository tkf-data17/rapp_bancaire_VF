
import os
import shutil
import extract_table
import config

def test_fix():
    print("Testing fix...")
    # Setup test dir
    test_dir = "test_extraction_source"
    os.makedirs(test_dir, exist_ok=True)
    
    # Copy relevé.pdf
    src = "relevé.pdf"
    dst = os.path.join(test_dir, "relevé.pdf")
    if os.path.exists(src):
        shutil.copy(src, dst)
        print(f"Copied {src} to {dst}")
    else:
        print(f"Source {src} not found!")
        return

    # Run extraction
    output_dir = "test_extraction_output"
    extract_table.batch_process_pdf_folder(source_dir=test_dir, output_dir=output_dir)
    
    # Verify output
    out_csv = os.path.join(output_dir, "relevé.csv")
    if os.path.exists(out_csv):
        print("\nChecking Output CSV Content for 979...")
        with open(out_csv, 'r', encoding='utf-8') as f:
            for line in f:
                if "979" in line or "29979" in line or "2979" in line:
                    print(f"CSV Line: {line.strip()}")
    else:
        print("Output CSV not found.")

if __name__ == "__main__":
    test_fix()
