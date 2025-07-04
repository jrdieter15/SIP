# Product Requirements Document (PRD)

**Project Title:** Nextcloud Talk SIPCall Integration  
**Version:** 1.0  
**Date:** 2025-01-27  
**Author:** Development Team

---

## 1. Purpose

The purpose of this project is to design and develop a self-hosted, secure, and privacy-focused SIP (PSTN) calling integration for Nextcloud Talk. This integration will enable users and teams to initiate and manage international PSTN calls within the Nextcloud Talk interface, using FreeSWITCH as the telephony core and a SIP trunk provider such as Telnyx.

---

## 2. Background

SIP Trip Phone and other similar apps provide basic SIP functionalities but suffer from limited maintenance, poor UI integration, audio-only support, and lack of scalability. This PRD outlines a more robust, secure, and user-friendly approach that aligns with GDPR, is scalable from individuals to enterprises, and avoids over-complexity.

---

## 3. Scope

### 3.1 In Scope

- Native integration with Nextcloud Talk
- PSTN call initiation via FreeSWITCH and SIP trunk
- Vue.js frontend UI embedded in Talk interface
- FastAPI backend for SIP routing and control
- PostgreSQL for storing call logs
- TLS/SRTP encryption for privacy
- Admin dashboard for usage analytics and trunk management

### 3.2 Out of Scope

- Video calling (Phase 2 or optional upgrade)
- Full CRM or address book functionality (to be integrated later)
- Call recording (intentionally excluded due to privacy risk)

---

## 4. User Personas

### Individual User
- Makes occasional international calls
- Values privacy and a simple interface

### Team Administrator
- Manages user permissions and tracks usage
- Needs compliance and monitoring tools

### Enterprise Manager
- Requires audit logs, analytics, multi-user control
- Seeks cost visibility and system health reports

---

## 5. Functional Requirements

### 5.1 Core Calling Features
- Dialpad interface with number validation
- Country code selector
- Real-time call status (e.g., connecting, in-progress)
- Call control buttons: Mute, Hold, Transfer
- Secure, encrypted call setup via FreeSWITCH

### 5.2 Admin Features
- User permission management
- Call cost dashboard (via Telnyx or similar API)
- Trunk configuration and monitoring
- System health indicators

### 5.3 Integration & API
- Use FastAPI backend with endpoints:
  - POST `/call` — Initiate call
  - GET `/call-status/{id}` — Get call status
  - POST `/log-call` — Save call to DB
  - POST `/auth` — Handle OAuth login
  - GET `/balance` — Check SIP provider credit
- Connect backend to FreeSWITCH via REST or socket API
- Embed frontend in Talk via native PHP app wrapper

---

## 6. Non-Functional Requirements

- Must run on a single VPS (4CPU/8GB minimum)
- Data must be encrypted at rest and in transit
- Support for at least 50 concurrent users
- Interface must be responsive (desktop and mobile)
- System must be fault-tolerant (auto-restart containers, retry calls)

---

## 7. Architecture Overview

- **Frontend:** Vue.js (embedded in Nextcloud via PHP wrapper)
- **Backend:** FastAPI (Python) — handles API logic and security
- **Telephony:** FreeSWITCH — SIP and PSTN bridging
- **SIP Provider:** Telnyx or VoIP.ms — PSTN call gateway
- **Database:** PostgreSQL — call logs and admin data
- **Deployment:** Docker containers on Ubuntu VPS
- **Security:** TLS/SRTP, OAuth2, JWT, CORS, rate limiting

---

## 8. Success Metrics

- Call completion rate > 95%
- Audio quality rating > 4.5/5
- System uptime > 99.9%
- First-call success rate > 90%
- Admin UI latency < 200ms

---

## 9. Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| FreeSWITCH misconfigurations | Use Dockerized, tested configs |
| Real-time status via polling | Use WebSocket upgrade where possible |
| Nextcloud update breakage | Test on stable version (v30.0.1) |
| Lack of SIP knowledge | Use community-verified modules (e.g., mod_verto) |

---

## 10. Timeline (6–8 weeks)

| Week | Milestone |
|------|-----------|
| 1 | Wireframes and requirements finalized |
| 2 | VPS setup, FreeSWITCH + Telnyx integration |
| 3 | Vue frontend prototype |
| 4 | FastAPI backend endpoints implemented |
| 5 | Nextcloud app wrapper and Talk integration |
| 6 | Admin dashboard and database integration |
| 7 | Security hardening, logging, optimization |
| 8 | Final QA, documentation, and deployment |