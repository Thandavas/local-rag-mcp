from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader

def get_chunks(pdfs):
    all_chunks = []
    for file in pdfs:
        loader = PyPDFLoader(file)
        docs = loader.load()
        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        chunks = splitter.split_documents(docs)
        all_chunks.extend(chunks)
    return all_chunks