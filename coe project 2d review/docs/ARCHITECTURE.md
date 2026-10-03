# System Architecture Specification

## Overview
The **Confidentiality-Aware Hospital Knowledge Summarisation and Sharing Assistant** is a clinical governance system designed for hospitals with shifting personnel and frequent protocol updates. It ensures that sensitive clinical protocols, incident reports, and medication codes are never leaked to unauthorised staff during document summarisation or peer-to-peer sharing.

---

## 1. System Component Diagram

```
+-------------------------------------------------------------------------+
|                              FRONTEND SPA                               |
|        HTML5 / Modern Vanilla CSS / JavaScript (Single Page App)        |
+-------------------------------------------------------------------------+
                                    |
                             REST API Calls
                                    v
+-------------------------------------------------------------------------+
|                             FASTAPI BACKEND                             |
|                                                                         |
|  +--------------------+   +-------------------+   +------------------+  |
|  |   Auth & RBAC      |   |  Redacted         |   | Sharing & Human  |  |
|  |   Permission       |   |  Summariser       |   | Confirmation     |  |
|  |   Engine           |   |  Engine           |   | Workflow         |  |
|  +--------------------+   +-------------------+   +------------------+  |
|                                                                         |
|  +--------------------+   +-------------------+   +------------------+  |
|  | Event Stream       |   | Experiment &      |   | Audit Logging    |  |
|  | Processor          |   | Leakage Suite     |   | System           |  |
|  +--------------------+   +-------------------+   +------------------+  |
+-------------------------------------------------------------------------+
                                    |
                               SQLAlchemy
                                    v
+-------------------------------------------------------------------------+
|                            SQLITE DATABASE                              |
|   (users, documents, document_sections, sharing_requests, audit_logs)   |
+-------------------------------------------------------------------------+
```

---

## 2. Security & RBAC Model

### Role Permission Matrix
| Role | Maximum Allowed Level | Accessible Documents |
| :--- | :--- | :--- |
| **Admin** | `HIGHLY_CONFIDENTIAL` | Public, Internal, Confidential, Highly Confidential |
| **Hospital Manager** | `CONFIDENTIAL` | Public, Internal, Confidential |
| **Doctor** | `CONFIDENTIAL` | Public, Internal, Confidential |
| **Nurse** | `CONFIDENTIAL` | Public, Internal, selected Confidential |
| **Receptionist** | `INTERNAL` | Public, selected Internal |
| **Intern** | `INTERNAL` | Public, limited Internal |

### Backend API Protection Enforcement
Document content redaction is enforced in the **backend Python API layer** before returning JSON payloads to the frontend.
If an unauthorised role requests details or summaries of sensitive sections, the backend strips the text and replaces it with `[REDACTED - SENSITIVE CONTENT WITHHELD FOR YOUR ROLE]`.

---

## 3. Event Stream Processing Architecture
To protect entity state from network delays, duplicate transmissions, or out-of-order events:
1. **Idempotency Check**: Uses `event_id` and sequence tracker. Duplicate event IDs return `IGNORED_DUPLICATE` with zero state mutation.
2. **Version Control**: Evaluates `event_version` against `last_processed_version`. Delayed events with `event_version <= last_processed_version` return `DISCARDED_STALE`.
3. **Out-of-Order Buffering**: Events with `event_version > last_processed_version + 1` are buffered in `OUT_OF_ORDER_BUFFERED` status and automatically drained in sequence order when missing intermediate events arrive.
