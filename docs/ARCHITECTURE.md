# NumberGuard System Architecture

## Overview

NumberGuard is a privacy-preserving B2B SaaS platform designed for telecom operators (Jio, Airtel, Vi, BSNL) to manage the lifecycle of decommissioned mobile subscriber numbers before they are safely recycled and reallocated to new subscribers.

```
+------------------------+        +--------------------------+
|  Telecom Operators     |        |  Digital Service Hubs    |
|  (Jio, Airtel, Vi)     |        |  (Banks, Fintechs, IdPs) |
+-----------+------------+        +-------------+------------+
            |                                   ^
     Ingestion Batch / Webhook                  | Pseudonymized Unlinking Alerts
            v                                   v
+------------------------------------------------------------+
|                   NumberGuard Core Platform                |
|                                                            |
|  +---------------------+        +-----------------------+  |
|  |   Privacy Enclave   |        |   Risk Engine         |  |
|  |   - Masking Engine  |        |   - Banking weighting |  |
|  |   - HMAC-SHA256     |        |   - Cooling progress  |  |
|  |   - Zero Identity   |        |   - Overdue SLA decay |  |
|  +----------+----------+        +-----------+-----------+  |
|             |                               |              |
|             v                               v              |
|  +---------------------+        +-----------------------+  |
|  |   Cooling Engine    |        |   Readiness Engine    |  |
|  |   - 60/90/120d Hold |        |   - Decision Matrix   |  |
|  |   - Auto-Extension  |        |   - Carrier Release   |  |
|  +---------------------+        +-----------------------+  |
|                                                            |
|  +------------------------------------------------------+  |
|  |       Immutable Audit Logging & RBAC Matrix          |  |
|  +------------------------------------------------------+  |
+------------------------------------------------------------+
```

## State Machine

1. **`DECOMMISSIONED`**: Carrier logs permanent disconnection of a SIM / MSISDN.
2. **`COOLING_HOLD`**: Standard statutory quarantine starts (60 days default, 90 days for banking, 120 days for high risk).
3. **`NOTIFYING_PROVIDERS`**: Pseudonym challenge notifications are dispatched to registered banks, fintechs, and services.
4. **`MANUAL_REVIEW` / `BLOCKED`**: Active unacknowledged alerts or high residual risk score prevents reallocation.
5. **`ELIGIBLE`**: Cooling period has elapsed, and zero high-risk unacknowledged alerts remain.
6. **`REALLOCATED`**: Approved and released back to carrier subscriber sales inventory.

## RBAC Roles

- `SUPER_ADMIN`: Regulatory platform oversight & global tenant provisioning.
- `TELECOM_ADMIN`: Operator management, cooling policy configuration, risk override sign-off.
- `TELECOM_OPERATOR`: Batch number intake, status review, and dispatch execution.
- `SERVICE_PROVIDER_ADMIN`: Bank / platform webhook configuration and SLA management.
- `SERVICE_PROVIDER_OPERATOR`: Remediation acknowledgment responder.
- `AUDITOR`: Regulatory read-only compliance inspection.
- `ANALYST`: Aggregate risk and trend insights.
