# REST API Reference Documentation

## Base URL
`http://127.0.0.1:8000/api`

---

## 1. Authentication & Users
* **`GET /api/auth/users`**: List all synthetic hospital users and active roles.
* **`GET /api/auth/user/{user_id}`**: Get user profile details.

---

## 2. Documents & Summaries
* **`GET /api/documents/?user_id={user_id}`**: List protocol documents with role access badges.
* **`GET /api/documents/{document_id}?user_id={user_id}`**: Get document details with backend-enforced section redactions.
* **`POST /api/documents/{document_id}/summarize?user_id={user_id}&use_baseline={bool}`**: Generate safe protocol summary.

---

## 3. Sharing & Human Approvals
* **`POST /api/sharing/evaluate`**: Pre-evaluate sharing risk and recommendation.
* **`POST /api/sharing/request`**: Submit sharing request.
* **`GET /api/sharing/requests`**: List sharing requests.
* **`POST /api/sharing/requests/{request_id}/decision`**: Process human approval/rejection with mandatory override reason.

---

## 4. Governance Audit Logs
* **`GET /api/audit/logs`**: Retrieve audit log entries for Admin review.

---

## 5. Event Stream Processor
* **`POST /api/events/inject`**: Inject event into stream processor (tests duplicate, delayed, and out-of-order handling).
* **`GET /api/events/stream`**: Get event stream log and entity version trackers.

---

## 6. Experiments & Validation
* **`GET /api/experiments/results`**: Fetch baseline vs proposed metrics and test cases.
* **`POST /api/experiments/run-suite`**: Trigger complete experiment suite.
* **`POST /api/experiments/run-leakage-test`**: Run automated synthetic leakage test.
* **`POST /api/validation/submit`**: Submit stakeholder feedback.
* **`GET /api/validation/summary`**: Get stakeholder validation summary analytics.
