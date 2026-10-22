# 🛢️ DrillSense: AI-Powered Operational Intelligence from Daily Drilling Reports

**DrillSense** is a **domain-specific LLM + RAG system** engineered to deliver **AI-based operational insights and alerts** from **Daily Drilling Reports (DDRs)** and associated petroleum engineering documentation.

It leverages a dual approach combining **Supervised Fine-Tuning (SFT)** for domain knowledge injection and a **Retrieval-Augmented Generation (RAG)** pipeline to ensure outputs are accurate, explainable, and contextually grounded.

-----

## 🚀 Key Capabilities

DrillSense is built on a **Large Language Model (LLM) fine-tuned on proprietary drilling data** and enhanced by retrieval-based context injection. It provides the following core functionalities:

  * **Automated Summarization:** Generates concise summaries of **daily drilling operations** and activities.
  * **Domain-Specific Q\&A:** Answers complex questions regarding **PVT (Pressure-Volume-Temperature) data** and well procedures.
  * **Context-Aware Alerting:** Provides LLM-based risk or **anomaly alerts** based on contextual information from the reports.
  * **Semantic Retrieval:** Enables highly accurate, domain-specific search and retrieval of past operations and documents.
  * **Full-Stack Deployment:** Integrated user experience delivered through a **React + FastAPI** deployment stack.

-----


## ⚙️ Technology Stack

| Layer | Technology | Purpose / Details |
| :--- | :--- | :--- |
| **Frontend** | React.js, Tailwind CSS, Axios, React Query | Responsive UI for query submission and results visualization. |
| **Backend** | FastAPI, Uvicorn, Python 3.9+ | High-performance, asynchronous REST API layer for serving requests. |
| **Vector Database** | **FAISS (HNSW)** | High-speed similarity search and vector storage for RAG. |
| **AI / ML** | **Vertex AI (SFT)**, **SentenceTransformers** | Model fine-tuning, managed deployment, and text embedding generation. |
| **RAG Pipeline** | Naive RAG (Retrieval $\rightarrow$ Prompt Composition $\rightarrow$ LLM) | Context injection mechanism to ground the LLM's responses. |
| **Deployment** | GCP VM, Nginx, Vercel | Backend hosting/proxying (GCP), Frontend hosting (Vercel). |
| **DevOps** | Docker, GitHub Actions | Containerization and CI/CD for streamlined deployments. |
| **Model Hosting** | Vertex AI Model Registry/Endpoints | Centralized, scalable hosting of the fine-tuned LLM. |

-----

## 🧠 AI & Data Workflow

### 1\. Supervised Fine-Tuning (SFT)

The foundational LLM is fine-tuned to master the specific language and concepts of petroleum engineering.

  * **Training Data Sources:**
      * `volve_daily_drilling_report`
      * `Whitson PVT Manual`
      * `volve_alpaca` (Used for instruction-tuning augmentation)
  * **Data Preprocessing:**
      * Cleaned placeholder values (e.g., `-999.99` converted to `null` or excluded).
      * De-identified sensitive or proprietary data.
      * Normalized field names and domain-specific tokens.
  * **Training & Evaluation:**
      * Split: **$80\%$ Train, $10\%$ Validation, $10\%$ Test**.
      * Training conducted on **Vertex AI**.
      * Achieved an initial **$\approx 68\%$ task accuracy** on the held-out validation set.

### 2\. Retrieval-Augmented Generation (RAG) Pipeline

The RAG pipeline provides up-to-date, precise context for the fine-tuned LLM.

  * **Document Processing:**
      * **Chunking Strategy:** 300–600 tokens with 80–100 token overlap.
      * **Embedding Model:** `all-MiniLM-L6-v2` (high-speed, effective sentence embedding).
  * **Retrieval:**
      * **Storage:** **FAISS** index utilizing the Hierarchical Navigable Small World (**HNSW**) algorithm.
      * **Search:** **Top-K** semantic similarity search ($\text{K}=5$) to retrieve the most relevant chunks.
  * **Prompt Composition (Fixed):**
    $$
    $$$$\\text{"Use ONLY the provided context to answer the question. Context: } {\\text{retrieved\_chunks}} \\text{ Question: } {\\text{user\_query}}"
    $$
    $$$$
    $$
  * **Output:** The LLM's final response is generated and displayed with source citations for verifiability.

-----


## 🧮 Key Performance Metrics

| Metric | Achieved Value | Description |
| :--- | :--- | :--- |
| **Task Accuracy (SFT)** | $\approx 68\%$ | Accuracy on the held-out validation set for the core tasks. |
| **System Error Rate** | $< 5\%$ | Proportion of requests resulting in a server or infrastructure error. |
| **$\text{P90}$ Latency (Target)** | $< 3.0 \text{ seconds}$ | Target time for $90\%$ of queries to be completed. |

-----

## 🛠️ Infrastructure & Deployment

  * **Frontend Deployment:**
      * Deployed and managed via **Vercel**.
      * Utilizes React/Tailwind and communicates with the backend via REST.
  * **Backend Deployment:**
      * Hosted on a **GCP VM Instance**.
      * Reverse-proxied through **Nginx** for security and load balancing.
      * FastAPI application served by **Uvicorn** and managed by **Supervisor**.
  * **Domain Configuration (Hostinger):**
      * `drill-sense.com` $\rightarrow$ Frontend (Vercel)
      * `api.drill-sense.com` $\rightarrow$ Backend (GCP VM)

-----

## 📊 Monitoring & Maintenance

  * **Continuous Monitoring:** Metric logging handled by **Prometheus** for collection and **Grafana** for visualization.
  * **Automated Retraining:**
      * Weekly evaluation process.
      * Triggers a full model retraining if **accuracy drops $>5\%$** or the **hallucination rate exceeds $>5\%$**.
  * **Deployment Safety:** **Canary deployment** ($5\%$ traffic test) is used before a full-scale model rollout.
  * **Security:** Endpoints are secured with **API keys** and enforced **rate limits**. Logs are **sanitized** (no PII/sensitive data) before storage.

-----

## 🧱 Project Deliverables

  * ✅ Cleaned & validated JSONL datasets for SFT.
  * ✅ SFT training and validation scripts.
  * ✅ FAISS embedding and index builder utility.
  * ✅ Modularized FastAPI backend with all defined endpoints.
  * ✅ React + Tailwind responsive frontend interface.
  * ✅ Dockerized backend deployment environment.
  * ✅ Integrated monitoring and auto-retrain pipeline.
  * ✅ Functional prototype hosted on Hugging Face Spaces.

-----

## 🧰 Example Usage

### Backend Query Example

```bash
# Run backend locally
uvicorn app.main:app --reload

# Query the /generate endpoint
curl -X POST "http://localhost:8000/generate" \
    -H "Content-Type: application/json" \
    -d '{"query": "Summarize the daily drilling activities for 2023-07-12"}'
```

The frontend automatically connects to the same `/api` routes via the `api.drill-sense.com` subdomain. Users can also interact directly by pasting their drilling reports on the web interface.

-----

## 📈 Future Work & Roadmap

  * **Advanced RAG:** Upgrade from naive RAG to a **hybrid RAG architecture** incorporating techniques like vector search and **cross-encoder re-ranking**.
  * **Proactive Alerting:** Integrate a classical ML model, such as **LightGBM**, for advanced time-series **anomaly detection** to augment LLM-based operational alerts.
  * **Feedback Loops:** Implement a robust mechanism for **domain feedback and human-in-the-loop validation** to continuously improve the SFT model.
  * **Scalable Vector Store:** Migrate the index deployment from local FAISS to a managed, scalable service like **Milvus** or **Pinecone** for enterprise readiness.

-----

## 🧑‍💻 Author

**Abdullah Imran**
AI Engineer | Data Scientist

Email: [abdullahimranarshad@gmail.com]
LinkedIn: [https://www.linkedin.com/in/abdullah--imran/](https://www.linkedin.com/in/abdullah--imran/)

GitHub: [https://github.com/poetabdullah](https://github.com/poetabdullah)

**Project developed for Avions AI**

-----

## 📄 License

This project is licensed under the **MIT License** — see the `LICENSE` file for details.
