# Payroll Pilot Assistant (No-DB Prototype)

This repository contains a **database-free pilot implementation** of the payroll support assistant described in the design diagram.

## What is implemented

- Employee chat interface (web UI)
- Rule-based NLP intent handling for common payroll questions
- Security & authentication gate (employee ID or token validation)
- Knowledge base retrieval from local in-memory data
- Payroll data retrieval from mock in-memory data
- Payslip summary generation (gross pay, deductions, net pay)
- HR escalation path when a query is sensitive/unknown
- In-memory metrics collection and reporting
- Placeholder update APIs for employee profile and bank changes

## API endpoints

- `GET /api/health`
  - Health status check.

- `POST /api/chat`
  - Authenticates request (`employee_id` or `token`) and processes chatbot messages.
  - Returns route, message, and `payslip_summary` for payroll queries.

- `GET /api/metrics`
  - Returns metrics:
    - `deflection_rate`
    - `average_response_time`
    - `error_rate`
    - `handoff_rate`

- `POST /api/update-address`
  - Placeholder endpoint that authenticates, logs request payload, and returns request receipt.

- `POST /api/update-bank`
  - Placeholder endpoint that authenticates, logs request payload, and returns request receipt.

## Auth model (pilot)

The pilot accepts:
- Employee IDs: `E1001`, `E1002`
- Tokens: `token-E1001`, `token-E1002`

Unauthorized requests receive a `401` JSON response:

```json
{ "error": "Unauthorized" }
```

## Run

```bash
python app.py
```

Open `http://localhost:8000`.

## Test

```bash
python -m unittest discover -s tests -p 'test_*.py'
```

## Future DB integration

Implement adapters that satisfy the interfaces in `src/payroll_support/repositories.py`:

- `KnowledgeRepository`
- `PayrollRepository`
- `TicketRepository`
- `MetricsRepository`

Then inject those adapters into `PayrollSupportService` in `app.py`.

## Repository structure

If you want to quickly verify the pilot files are present, you should see:

- `app.py`
- `src/payroll_support/`
  - `engine.py`
  - `security.py`
  - `repositories.py`
  - `service.py`
- `tests/`
  - `test_service.py`
  - `test_app_api.py`
- `web/`
  - `index.html`
  - `app.js`
  - `styles.css`

You can also run:

```bash
rg --files
```

and

```bash
git log --oneline -n 5
```

to confirm the committed files and recent history locally.
