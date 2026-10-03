# Confidentiality-Aware Hospital Knowledge Summarisation & Sharing Assistant

[![Python Version](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/framework-FastAPI-teal.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

An end-to-end, confidentiality-aware clinical protocol summarisation and sharing system designed for hospital shift workers and protocol updates. It enforces role-based access control (RBAC), prevents sensitive data leakage, mandates human confirmation with written override reasons for high-impact sharing, and processes event streams safely against network delays, duplicates, and out-of-order delivery.

---

## 📋 Table of Contents
- [Project Overview](#project-overview)
- [Problem Statement](#problem-statement)
- [Architecture & Tech Stack](#architecture--tech-stack)
- [Installation & Setup](#installation--setup)
- [Database Initialization & Data Generation](#database-initialization--data-generation)
- [How to Run the Application](#how-to-run-the-application)
- [How to Run Experiments & Leakage Tests](#how-to-run-experiments--leakage-tests)
- [How to Run Automated Unit Tests](#how-to-run-automated-unit-tests)
- [API Overview](#api-overview)
- [Security & Permission Model](#security--permission-model)
- [Event Stream Processor](#event-stream-processor)
- [Failure & Edge Case Handling](#failure--edge-case-handling)
- [Known Limitations](#known-limitations)

---

## 🏥 Project Overview
Hospitals experience frequent protocol changes and personnel working in shifts. Confidential information (such as internal incident reviews, controlled drug vault codes, patient pseudonyms, and malpractice investigation notes) can accidentally be exposed when protocols are summarised or shared with staff who are not authorised to see sensitive data.

This assistant:
1. Label documents with permission classifications (`PUBLIC`, `INTERNAL`, `CONFIDENTIAL`, `HIGHLY_CONFIDENTIAL`).
2. Enforces user role permissions (`Admin`, `Hospital Manager`, `Doctor`, `Nurse`, `Receptionist`, `Intern`).
3. Summarises documents from permitted sections only, redacting sensitive content BEFORE sending to client APIs.
4. Explains why content was withheld in simple non-specialist language (Rule, Reason, Evidence).
5. Routes high-risk sharing requests for human approval.
6. Mandates written override justifications for human approvals.
7. Logs all actions to an immutable audit trail.
8. Handles delayed, duplicate, and out-of-order event streams without state corruption.

---

## 🛠️ Architecture & Tech Stack
- **Frontend**: HTML5, Vanilla CSS3 (Glassmorphism design system), Modern Vanilla JS (Single-Page Application).
- **Backend**: Python 3.11, FastAPI REST Web Framework, Uvicorn Server.
- **Database**: SQLite with SQLAlchemy 2.0 ORM.
- **Testing & Data**: Pytest, Pandas, Synthetic Data Generator.

---

## 🚀 Installation & Setup

### Prerequisites
- Python 3.11+

### Installation Commands
```bash
# Clone or navigate to the project directory
cd "c:/Users/ADMIN/Desktop/coe project 2d review"

# Install dependencies
py -3 -m pip install -r requirements.txt
```

---

## 📊 Database Initialization & Data Generation
Generate synthetic hospital data and initialize the SQLite database:
```bash
# Generate synthetic CSV datasets in data/synthetic/
py -3 scripts/generate_data.py

# Initialize database schema & seed tables
py -3 backend/app/database_init.py
```

---

## 🖥️ How to Run the Application

### Option A: Run Server via Python (Recommended)
```bash
py -3 -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
Once started, open your browser and navigate to:
**`http://127.0.0.1:8000`**

FastAPI Interactive API Documentation is available at:
**`http://127.0.0.1:8000/docs`**

---

## 🧪 How to Run Experiments & Leakage Tests

### 1. Run Synthetic Leakage Test
Evaluates baseline vs proposed system leakage rate across unauthorised user roles:
```bash
py -3 scripts/run_leakage_tests.py
```

### 2. Run Complete Experiment Suite
Measures all baseline comparison metrics and saves results to `experiments/results.json`:
```bash
py -3 scripts/run_experiment.py
```

---

## 🚦 How to Run Automated Unit Tests
Run full system verification test suite using `pytest`:
```bash
py -3 -m pytest backend/tests/test_all_features.py -v
```

---

## 🔑 Security & Permission Model
- **Admin**: All confidentiality levels (`PUBLIC`, `INTERNAL`, `CONFIDENTIAL`, `HIGHLY_CONFIDENTIAL`).
- **Hospital Manager**: `PUBLIC`, `INTERNAL`, `CONFIDENTIAL`.
- **Doctor**: `PUBLIC`, `INTERNAL`, `CONFIDENTIAL`.
- **Nurse**: `PUBLIC`, `INTERNAL`, selected `CONFIDENTIAL`.
- **Receptionist**: `PUBLIC`, selected `INTERNAL`.
- **Intern**: `PUBLIC`, limited `INTERNAL`.

Backend APIs enforce access control strictly. Redactions are performed in Python on the server side prior to JSON serialization.

---

## ⚡ Event Stream Processor
Handles event sequence disruptions:
- **Duplicate Events**: Idempotent check on `event_id` returns `IGNORED_DUPLICATE`.
- **Out-of-Order Events**: Future versions stored in `OUT_OF_ORDER_BUFFERED` and drained sequentially.
- **Delayed Events**: Stale versions (`event_version <= last_processed_version`) discarded as `DISCARDED_STALE`.

---

## 📌 Known Limitations
- LLM summarization is currently simulated via deterministic semantic rule-based summarisation for reproducible offline demonstration.
- SQLite is used for local single-file data storage; production deployments should use PostgreSQL with row-level security.
