# Failure Mode & Edge Case Analysis Report

## Overview
This document analyzes 7 explicit edge case scenarios tested against the system to ensure robust operational resilience in clinical environments.

---

## 1. Edge Case Test Matrix

### CASE 1: Unauthorised User Requests Confidential Summary
* **Scenario**: Intern requests summary of Shift Handover Protocol `DOC-HND-005` containing sensitive incident notes.
* **Expected Result**: Sensitive content withheld; safe redacted summary generated.
* **Actual Result**: Summary generated with 1 sensitive section withheld. Explanation displayed.
* **Status**: **PASSED**

### CASE 2: Unauthorised Sharing Request
* **Scenario**: Nurse attempts to share Confidential ICU Protocol `DOC-ICU-006` with an Intern.
* **Expected Result**: Sharing blocked or routed for mandatory human review with HIGH risk warning.
* **Actual Result**: Request created in `PENDING` status. System displays "Access not recommended."
* **Status**: **PASSED**

### CASE 3: Human Override Without Justification
* **Scenario**: Reviewer clicks APPROVE on restricted sharing request without filling the override reason box.
* **Expected Result**: System rejects empty override reason and blocks state change.
* **Actual Result**: Backend returned HTTP 400 Bad Request with message `Override reason is MANDATORY`.
* **Status**: **PASSED**

### CASE 4: Duplicate Sharing Event Arrival
* **Scenario**: Network retry sends duplicate event `EVT-TEST-DUP-01` with identical event ID.
* **Expected Result**: Idempotent processing; status `IGNORED_DUPLICATE` with 0 state changes.
* **Actual Result**: First event `PROCESSED`, second event `IGNORED_DUPLICATE`.
* **Status**: **PASSED**

### CASE 5: Out-of-Order Event Sequence
* **Scenario**: Event v3 arrives before intermediate event v2.
* **Expected Result**: Event v3 buffered; upon v2 arrival, v2 and v3 applied sequentially.
* **Actual Result**: Event v3 status `OUT_OF_ORDER_BUFFERED`. Upon v2 injection, both drained to `PROCESSED`.
* **Status**: **PASSED**

### CASE 6: Delayed Event Arrival
* **Scenario**: Delayed event v1 arrives after document permission updated to v3.
* **Expected Result**: Delayed event discarded as `DISCARDED_STALE` to protect current active state.
* **Actual Result**: Processing status returned `DISCARDED_STALE`.
* **Status**: **PASSED**

### CASE 7: Outdated Protocol Version Requested
* **Scenario**: Staff member requests legacy protocol `DOC-INF-000` (v1.0).
* **Expected Result**: System displays warning `This protocol has been superseded` and recommends active version v2.1.
* **Actual Result**: Response contains `SUPERSEDED` status and recommended active version ID.
* **Status**: **PASSED**
