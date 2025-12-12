# Multimodal RAG API and Frontend

This project implements a full-stack **Multimodal Retrieval-Augmented Generation (RAG)** application.

*   **Backend:** A **FastAPI** application that supports ingesting and querying both **text** and **image** data. It uses **CLIP embeddings**, a vector database (**Pinecone** or in-memory fallback), and a multimodal Large Language Model (**Google Gemini**) for generative answers.
*   **Frontend:** A **React** application that provides a user interface to interact with the backend API. Users can upload documents, run queries, and view the results.

The backend is structured to handle two types of knowledge bases:

*   **GKB (General Knowledge Base):** Publicly accessible data.
*   **SKB (Specific Knowledge Base):** User-specific and isolated data, keyed by the authenticated user's email.

-----

## 🚀 Key Features

*   **Multimodal Embeddings:** Uses the **CLIP** model (`openai/clip-vit-base-patch32`) to generate vector representations for both text and images.
*   **RAG Pipeline:** Orchestrates the flow from query embedding, vector search, content retrieval from S3, and final generation using **Gemini**.
*   **Document Processing:** Includes a service to extract **text and images from PDF** documents using PyMuPDF.
*   **Scalable Storage:** Uses **AWS S3** for persistent storage of original text and image files.
*   **Authentication:** Secured with **JWT** using OAuth2 Password Flow.
*   **React Frontend:** A user-friendly interface for interacting with the RAG pipeline.

-----

## 📁 Project Structure

The codebase is organized as follows:

```
.
├── README.md
├── requirements.txt      # Python dependencies for the backend
├── backend/
│   └── app/              # FastAPI backend source code
│       ├── main.py
│       ├── api/
│       ├── core/
│       ├── db/
│       ├── scripts/
│       └── services/
└── frontend/
    ├── package.json      # Node.js dependencies for the frontend
    └── src/              # React frontend source code
        ├── components/
        ├── services/
        └── App.jsx
```

-----

## ⚙️ Local Development Setup

### Prerequisites

*   Python 3.9+
*   Node.js and npm (or yarn)
*   Access to:
    *   **Google Gemini API** (for `GOOGLE_API_KEY`)
    *   **Pinecone** (optional, an in-memory mock is used if not configured)
    *   **AWS S3** (optional, for storage)

### 1. Clone the Repository

```bash
git clone https://github.com/adithya95978/multimodal-RAG.git
cd multimodal-RAG
```

### 2. Backend Setup

1.  **Create and activate a virtual environment:**
    ```bash
    cd backend
    python -m venv venv
    # On Linux/macOS
    source venv/bin/activate
    # On Windows
    .\venv\Scripts\activate
    ```

2.  **Install Python dependencies:**
    ```bash
    pip install -r ../requirements.txt
    ```

3.  **Configure Environment Variables**

    Create a file named `.env` in the `backend` directory (`multimodal-RAG/backend/.env`) and populate it with your credentials. Refer to `backend/app/core/config.py` for required variables:

    ```ini
    # .env file

    # Google Generative AI
    GOOGLE_API_KEY="YOUR_GOOGLE_API_KEY"

    # Pinecone (Optional - In-memory adapter used if keys are missing)
    PINECONE_API_KEY="YOUR_PINECONE_API_KEY"
    PINECONE_ENVIRONMENT="YOUR_PINECONE_ENVIRONMENT"
    # PINECONE_INDEX_NAME defaults to "multi-rag-index"

    # AWS S3 (Optional - Storage Service disabled if keys are missing)
    AWS_ACCESS_KEY_ID="YOUR_AWS_ACCESS_KEY_ID"
    AWS_SECRET_ACCESS_KEY="YOUR_AWS_SECRET_ACCESS_KEY"
    AWS_REGION="YOUR_AWS_REGION"
    S3_BUCKET_NAME="YOUR_S3_BUCKET_NAME"

    # Authentication (Change SECRET_KEY in production!)
    SECRET_KEY="a_very_secret_key_that_should_be_changed"
    ```

### 3. Frontend Setup

1.  **Navigate to the frontend directory:**
    ```bash
    cd frontend
    ```

2.  **Install Node.js dependencies:**
    ```bash
    npm install
    ```

### 4. Running the Application

1.  **Run the Backend Server:**

    From the `backend` directory (with the virtual environment activated):
    ```bash
    uvicorn app.main:app --reload
    ```
    The backend API will be available at `http://127.0.0.1:8000`.

2.  **Run the Frontend Development Server:**

    In a new terminal, from the `frontend` directory:
    ```bash
    npm run dev
    ```
    The frontend application will be available at `http://127.0.0.1:5173`.

-----

## 🛠 Usage and Endpoints

The API documentation (Swagger UI) is available at `http://127.0.0.1:8000/docs` when the backend is running.

### Authentication

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/auth/token` | Generates a JWT **access token** upon successful username/password (**`form_data.username`** is the email, e.g., `test@example.com`). |
| `GET` | `/api/v1/auth/users/me/` | Retrieves the details of the **current active user**. |

### Core API

All core endpoints (except health check) require a valid JWT `Authorization: Bearer <token>` header.

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/` | **Health Check** and displays a welcoming message. |
| `POST`| `/api/v1/embeddings/` | Creates a vector embedding for the provided **`text`** or **`image`** and upserts it to the **GKB** or **SKB**. |
| `POST`| `/api/v1/documents/extract/` | Extracts text and images from an uploaded **PDF** file. |
| `POST`| `/api/v1/query/` | Performs the full **RAG pipeline** by finding relevant context (text/image) based on the **`query`** and generating an answer. |

### Bulk Ingestion Script

The `bulk_ingest_gkb.py` script is a command-line utility for mass ingestion of PDF files into the **GKB** (General Knowledge Base).

1.  **Run the script:**
    ```bash
    python backend/app/scripts/bulk_ingest_gkb.py <path_to_pdf_or_directory>
    ```
2.  The script will:
      * Extract text and images from each PDF.
      * Upload the original content to **AWS S3**.
      * Create and upsert embeddings for both the text and images into the vector database.
