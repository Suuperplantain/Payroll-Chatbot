# Payroll Pilot Assistant

Payroll Pilot Assistant is a backend payroll chatbot API that answers supported payroll questions from an Excel payslip dataset.

The system is designed to:
- authenticate employees by `employee_id` or demo token,
- answer payroll-value questions from the dataset,
- return the latest payslip for an employee when multiple payslip rows exist,
- and offer HR handoff for unsupported questions.

## Current Status

This project is currently in progress.

## What The Backend Does

The backend currently supports these payroll query types:
- full payslip summary
- employee details
- tax code
- pay date
- pay period
- gross salary
- net pay
- PAYE tax
- National Insurance
- pension
- student loan
- healthcare scheme
- total deductions

If a user asks something outside those supported payroll queries, the chatbot responds politely and asks whether the user would like to be put in touch with HR. If the user confirms, the request is stored in the HR request database.

## Data Sources

### Payroll Data

Payroll answers come from `payslip.xlsx`.

The workbook is expected to use a row-based format with these columns:
- `employee_id`
- `employee_name`
- `job_title`
- `pay_period`
- `pay_date`
- `tax_code`
- `gross_salary`
- `paye_tax`
- `national_insurance`
- `pension`
- `student_loan`
- `healthcare_scheme`
- `net_pay`

Optional column:
- `total_deductions`

If `total_deductions` is blank, the backend calculates it from the deduction fields.

### HR Request Database

Confirmed HR handoff requests are stored in `hr_requests.db`.

The database stores:
- `employee_id`
- `hr_query`
- `sent_at`

## API Endpoints

### `GET /api/health`
Returns the API health status.

### `POST /api/chat`
Authenticates the user and processes payroll chatbot messages.

Response fields:
- `status`
- `route`
- `message`
- `data`
- `awaiting_confirmation`

Possible routes:
- `payroll`
- `security`
- `request`
- `hr_offer`
- `hr_escalation`

### `GET /api/metrics`
Returns backend interaction metrics:
- `deflection_rate`
- `average_response_time`
- `error_rate`
- `handoff_rate`
- `offer_rate`

## Authentication

The backend authorizes employee IDs found in the spreadsheet.

Demo tokens follow this format:

```text
token-<employee_id>
```

Unauthorized requests return a `401` response.

## Run

```bash
python app.py
```

The API runs on:

```text
http://localhost:8000
```

## Test

```bash
python -m unittest discover -s tests -p 'test_*.py'
```

## Project Structure

```text
app.py
payslip.xlsx
hr_requests.db
src/payroll_support/
tests/
```

## Notes

- This repository is backend-only.
- The chatbot does not guess answers outside the supported payroll fields.
- HR requests are only stored after the user confirms they want to be put in touch with HR.

