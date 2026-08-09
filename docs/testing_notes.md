# GarudaAI Testing & Scoping Notes

This document provides details on GarudaAI testing practices, test execution steps, and known project constraints.

---

## Automated Test Suite

We utilize the standard Python `unittest` framework to execute unit and integration tests covering the scoring engine, database collections, and Flask API routing.

### Test Execution Command
Run the test suite from the project root:
```bash
python -m unittest tests/test_backend.py
```

### Coverage Scope
1. **Scoring Engine Unit Tests**: Verify point deduction math for after-hours login, unknown device login, and restricted file accesses.
2. **Scoring Engine Recalculation Tests**: Verify chronological score evaluation, recovery score increases during behavior gaps, and history persistence.
3. **API Integration Tests**:
   - `GET /api/health`: Verify container status and active connection modes.
   - `GET /api/employees`: Verify return profile formats and sorting configurations.
   - `GET /api/employees/:id/timeline`: Verify collapsed chronological data retrieval.
   - `GET /api/alerts`: Verify threat alert query results.
4. **End-to-End Simulation Tests**: Verify that invoking `POST /api/simulate` reset collections, injects events, runs score engine recalculation, publishes alert, and returns the modified current score.

---

## Manual / Smoke Testing checklist

We perform smoke checks on the React frontend locally to verify visual fidelity and responsiveness:
- **Empty States**: Verify that searching for a non-existent ID displays a clean "No employees found" text panel.
- **Loading States**: Inspect spinners during profile deep-dives or AI playbooks loading.
- **Simulator Actions**: Verify that clicking "Inject Simulation Scenario" immediately refreshes the active timeline, alert feed, and Chart.js Line chart.
- **AI Security Chat**: Verify that typing "show employees below 50" returns the filtered profiles list in the chat box.

---

## Known Project Scoping Limitations

> [!WARNING]
> These scoping limitations are intentionally configured to support ease of evaluation and hackathon speed:

1. **File-Based JSON Fallback Database**:
   - *Behavior*: If MongoDB is not running locally, the backend switches to JSON files under `backend/mock_db/`.
   - *Limitation*: JSON storage is not thread-safe. Concurrent writes during multi-user testing will lock or overwrite files. Real production scaling requires a live MongoDB Atlas instance.
2. **Gemini API Key Fallback**:
   - *Behavior*: If the `GEMINI_API_KEY` is not present, the assistant falls back to a rule-based mock generator.
   - *Limitation*: Fallback reports are static template text for the 6 primary threat patterns. Real-time dynamic analysis requires configuring a valid Gemini API key in the `.env` file.
3. **Firebase Authentication Developer Bypass**:
   - *Behavior*: When `DEV_MODE=true` is enabled, Firebase JWT verification middleware is bypassed on all API routes.
   - *Limitation*: Local Vite client queries the APIs directly without passing security tokens. Production deployments must toggle `DEV_MODE=false` and provide the Firebase Private Key variables.
