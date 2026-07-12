import os

def handle_upload(input_data):
    # New logic: get all PDF files from data/documents
    pdf_dir = "data/documents"
    pdf_files = [
        f for f in os.listdir(pdf_dir)
        if f.lower().endswith(".pdf")
    ]

    input_data["files"] = pdf_files
    return input_data

test_input = {}
result = handle_upload(test_input)
print(result)