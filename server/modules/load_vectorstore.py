import os
import time
from pathlib import Path

from dotenv import load_dotenv
from tqdm.auto import tqdm
from pinecone import Pinecone, ServerlessSpec
from langchain_community.document_loaders import PyPDFLoader
from langchain_classic.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings


load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

# Pinecone serverless region
PINECONE_ENV = "us-east-1"

# IMPORTANT:
# Pinecone index names can only contain lowercase letters,
# numbers, and hyphens.
PINECONE_INDEX_NAME = "medical-index"


if GOOGLE_API_KEY is None:
    raise ValueError("GOOGLE_API_KEY is not set")

if PINECONE_API_KEY is None:
    raise ValueError("PINECONE_API_KEY is not set")

os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY


# Directory where uploaded PDFs are stored
UPLOAD_DIR = "./uploaded_docs"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# Initialize Pinecone
pc = Pinecone(api_key=PINECONE_API_KEY)

spec = ServerlessSpec(
    cloud="aws",
    region=PINECONE_ENV
)

existing_indexes = [i["name"] for i in pc.list_indexes()]


# Create index if it doesn't already exist
if PINECONE_INDEX_NAME not in existing_indexes:
    print(f"Creating Pinecone index: {PINECONE_INDEX_NAME}")

    pc.create_index(
        name=PINECONE_INDEX_NAME,
        dimension=3072,
        metric="dotproduct",
        spec=spec
    )

    # Wait until the index is ready
    while not pc.describe_index(PINECONE_INDEX_NAME).status["ready"]:
        time.sleep(1)

    print("Pinecone index is ready.")


# Connect to the index
index = pc.Index(PINECONE_INDEX_NAME)


def load_vectorstore(uploaded_files):

    embed_model = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001"
    )

    file_paths = []

    # --------------------------------------------------
    # Save uploaded files
    # --------------------------------------------------

    for file in uploaded_files:
        save_path = Path(UPLOAD_DIR) / file.filename

        with open(save_path, "wb") as f:
            f.write(file.file.read())

        file_paths.append(str(save_path))

    # --------------------------------------------------
    # Load and split PDFs
    # --------------------------------------------------

    for file_path in file_paths:

        loader = PyPDFLoader(file_path)
        documents = loader.load()

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=100
        )

        chunks = splitter.split_documents(documents)

        texts = [chunk.page_content for chunk in chunks]
        metadata = [
            {**chunk.metadata, "text": chunk.page_content}
            for chunk in chunks
        ]

        ids = [
            f"{Path(file_path).stem}-{i}"
            for i in range(len(chunks))
        ]

        # --------------------------------------------------
        # Generate embeddings
        # --------------------------------------------------

        print(f"Generating embeddings for {file_path}...")

        embeddings = embed_model.embed_documents(texts)

        # --------------------------------------------------
        # Upsert into Pinecone
        # --------------------------------------------------

        print("Upserting embeddings to Pinecone...")

        vectors = list(
            zip(
                ids,
                embeddings,
                metadata
            )
        )

        with tqdm(
            total=len(vectors),
            desc="Upserting to Pinecone"
        ) as progress:

            index.upsert(vectors=vectors)

            progress.update(len(vectors))

        print(f"Upload complete for {file_path}")
