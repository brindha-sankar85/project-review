# Baseline vs Proposed System Experiment Report

## 1. Executive Summary
An automated evaluation suite was executed to compare the **Experimental Baseline System** (unfiltered summariser) against the **Proposed Confidentiality-Aware System** (RBAC & section redaction engine).

Synthetic test markers (`SENSITIVE_TEST_001`, `RESTRICTED_TEST_002`, `HIGHLY_CONFIDENTIAL_TEST_003`) were injected into protocol documents and evaluated across unauthorised user roles (Nurse, Receptionist, Intern).

---

## 2. Experimental Metric Comparison Table

| Metric | Experimental Baseline | Target | Proposed System | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Sensitive Leakage Rate** | 100.0% | 0.0% | **0.0%** | **PASSED** |
| **Unauthorised Exposure Count** | 12 incidents | 0 | **0 incidents** | **PASSED** |
| **Access Control Accuracy** | 45.0% | 100.0% | **100.0%** | **PASSED** |
| **Safe Summary Rate** | 20.0% | 100.0% | **100.0%** | **PASSED** |
| **Duplicate Event Recovery** | 0.0% | 100.0% | **100.0%** | **PASSED** |
| **Out-of-Order Recovery Rate** | 0.0% | 100.0% | **100.0%** | **PASSED** |
| **Delayed Event Recovery Rate** | 0.0% | 100.0% | **100.0%** | **PASSED** |
| **Human Override Count** | 0 records | N/A | **1+ records** | **PASSED** |

---

## 3. Synthetic Leakage Test Methodology
1. **Test Population**: 9 Protocol Documents x 3 Unauthorised User Roles.
2. **Baseline Execution**: Raw document text passed directly to summary generator. Resulted in **100% leakage** of sensitive vault codes and patient pseudonyms.
3. **Proposed System Execution**: Document sections filtered through RBAC permission matrix. Resulted in **0.0% leakage** in protected scenarios.
