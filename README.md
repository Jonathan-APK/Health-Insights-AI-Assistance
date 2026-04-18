# Health Insight AI

> ⚠️ This project was developed as part of a course project.

## 📌 Overview

**Health Insight AI** is an AI-powered system designed to help users better understand complex healthcare information such as clinical reports and lab results.

Medical documents are often written in technical language that is difficult for non-experts to interpret. This project aims to bridge that gap by translating clinical data into clear, understandable insights while ensuring safety, privacy, and reliability. The results are not intended for medical diagnosis or professional healthcare use.

---

## 🚀 Project Objectives

This system is designed to:

- Interpret clinical documents and extract key findings  
- Translate results into understandable risk-level insights  
- Support conversational Q&A interactions  
- Remove sensitive information (PII) before processing  
- Enforce safety via input validation and compliance checks  

---

## 🧠 Key Features

- **Multi-agent AI workflow** for structured and explainable processing  
- **Input Guardrail Agent** to validate and filter unsafe or irrelevant inputs  
- **Document Parsing Service** to extract and preprocess text from PDF documents
- **PII Removal Service** to protect sensitive user data  
- **Orchestrator Agent** to make routing decisions
- **Clinical Analysis Agent** for interpreting medical data  
- **Risk Assessment Agent** to translate findings into risk insights  
- **Insight Generation Agent** to translate clinical data into clear, understandable insights
- **Q&A Agent** to answer questions from user  
- **Compliance Agent** to validate outputs against safety rules and ensure responses are appropriate and policy-compliant
- **Observability & Prompt Management** for LLM monitoring  

---

## 🏗️ System Architecture

The system follows a **multi-agent architecture**, where each component is responsible for a specific task in the processing pipeline:

- **Input Guardrail Agent** → validates and filters unsafe or irrelevant user inputs  
- **Document Parsing Service** → extracts and preprocesses text from PDF documents  
- **PII Removal Service** → removes sensitive information before downstream processing  
- **Orchestrator Agent** → manages workflow and makes routing decisions between agents  
- **Clinical Analysis Agent** → interprets clinical data and extracts key findings  
- **Risk Assessment Agent** → evaluates findings and assigns risk levels  
- **Insight Generation Agent** → converts clinical outputs into clear, user-friendly insights  
- **Q&A Agent** → handles follow-up user queries through conversational interaction  
- **Compliance Agent** → validates outputs against safety rules to ensure responses are appropriate and policy-compliant  

Agents communicate through shared state using a graph-based workflow, enabling conditional routing, modular execution, and better control over the overall system.

---

## ⚙️ Tech Stack

### Backend
- Python 3.12  
- FastAPI (async API framework)  
- LangGraph (workflow orchestration)  
- LangChain (LLM integration)  

### AI / LLM
- OpenAI GPT-4o-mini (classification & reasoning)  

### Storage
- Redis (session storage with TTL)  

### Observability
- Langfuse (tracing, monitoring, prompt management)  

### Infrastructure (AWS)
- S3 (frontend hosting)  
- CloudFront (CDN)  
- ECS Fargate (containerized backend)  
- Application Load Balancer (traffic routing)  
- ECR (container registry)  
- Secrets Manager (secure key storage)  
- CloudWatch (logging & monitoring)  

---

## 🔧 How It Works

1. User uploads a document or submits a query  
2. Input Guardrail validates and sanitizes the request  
3. PII is removed before processing  
4. The system routes the request through multiple agents  
5. Each agent performs a specific task  
6. Final insights are generated and returned to the user  

---

## 💡 Design Decisions

- **Async backend (FastAPI)**  
  → handles long-running LLM calls efficiently  

- **SSE over WebSockets**  
  → simpler real-time streaming for one-way updates  

- **Redis for session state**  
  → low-latency, auto-expiring session management  

- **Single container deployment**  
  → reduces complexity and latency for MVP  

---


## 🔮 Future Improvements

- More robust evaluation (e.g. hallucination detection)  
- LLM-as-a-judge scoring for output quality  
- Expanded test coverage (edge cases & adversarial inputs)  
- Improved guardrail logic for stronger safety enforcement  
- Support for more document formats beyond PDF  

---

## 📎 Disclaimer

This project is for educational purposes only and is **not intended for medical diagnosis or professional healthcare use**.
