import chromadb
import ollama
from pathlib import Path


def chunk_text(text, chunk_size=400, overlap=50):

    chunks = []
    start = 0

    while start < len(text):

        end = start + chunk_size
        chunk = text[start:end]

        chunks.append(chunk)

        start += chunk_size - overlap

    return chunks


class RAGEngine:

    def __init__(self):

        self.client = chromadb.PersistentClient(path="storage")

        # Separate knowledge sources
        self.guideline_collection = self.client.get_or_create_collection(
            name="medical_guidelines"
        )

        self.report_collection = self.client.get_or_create_collection(
            name="patient_reports"
        )

    def embed_text(self, text: str):

        response = ollama.embeddings(
            model="nomic-embed-text",
            prompt=text
        )

        return response["embedding"]

    # -----------------------------
    # Index medical guideline docs
    # -----------------------------
    def index_documents(self, folder_path="Medical_documents"):

        for file in Path(folder_path).glob("*.txt"):

            with open(file, "r", encoding="utf-8") as f:
                content = f.read()

            chunks = chunk_text(content)

            for i, chunk in enumerate(chunks):

                if not chunk.strip():
                    continue

                embedding = self.embed_text(chunk)

                doc_id = f"{file.stem}_{i}"

                try:
                    self.guideline_collection.delete(ids=[doc_id])
                except:
                    pass

                self.guideline_collection.add(
                    documents=[chunk],
                    embeddings=[embedding],
                    ids=[doc_id]
                )

        print("Medical guidelines indexed")

    # -----------------------------
    # Index uploaded patient report
    # -----------------------------
    def index_patient_report(self, patient_id, text):

        chunks = chunk_text(text)

        for i, chunk in enumerate(chunks):

            if not chunk.strip():
                continue

            embedding = self.embed_text(chunk)

            doc_id = f"{patient_id}_report_{i}"

            self.report_collection.add(
                documents=[chunk],
                embeddings=[embedding],
                ids=[doc_id]
            )

        print("Patient report indexed")

    # -----------------------------
    # Multi-source retrieval
    # -----------------------------
    def retrieve(self, query: str, n_results=3):

        query_embedding = self.embed_text(query)

        guideline_results = self.guideline_collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )

        report_results = self.report_collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )

        docs = []

        # Medical guidelines
        if guideline_results["documents"]:
            for doc in guideline_results["documents"][0]:

                docs.append({
                    "source": "medical_guideline",
                    "content": doc
                })

        # Patient reports
        if report_results["documents"]:
            for doc in report_results["documents"][0]:

                docs.append({
                    "source": "patient_report",
                    "content": doc
                })

        return docs