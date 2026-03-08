from setuptools import setup, find_packages

setup(
    name="patient_rag_assistant",
    version="0.1.0",
    description="RAG-based Patient Medical Assistant using Ollama and Chroma",
    author="Your Name",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "ollama",
        "chromadb",
        "pydantic",
        "sqlalchemy",
        "streamlit",
        "python-dotenv",
        "tqdm",
    ],
    python_requires=">=3.9",
)