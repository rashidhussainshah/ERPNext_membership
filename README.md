# Membership Dues

A Frappe app for clubs, lodges, associations and nonprofits to manage **members** and **dues payments**.
Each member's paid period and status are worked out automatically.

It runs on **plain Frappe** as a standalone module. When **ERPNext** is installed on the same site, it
also links members to ERPNext Customers.

## Features

| Area | What it does |
|---|---|
| **Membership Types** | Fee, duration in months and a grace period, e.g. *Annual: 120, 12 months, 30 days grace* |
| **Members** | Contact details, membership type and a status that is calculated: Applicant → Active → Lapsed |
| **Dues Payments** | Submittable payments; each one works out the exact period it covers |
| **Member actions** | Managers can **Suspend**, **Resign** and **Reinstate** members, with the reason logged |
| **Daily job** | Marks members **Lapsed** once their paid period and grace period have ended |
| **Report** | *Member Dues Status*: filters, days left, a status chart and summary cards |
| **REST API** | Member status lookup and an idempotent "record payment" endpoint for websites and payment gateways |
| **ERPNext link** | Adds a *Customer* field to Member and a **Create Customer** button (only if ERPNext is installed) |

## Business rules

| Situation | Result |
|---|---|
| First payment | Period starts on the payment date |
| Renewal while still paid up | New period starts the day after the current one ends, so no days are lost |
| Late renewal **within** the grace period | Continues from the old end date, so membership stays continuous |
| Late renewal **after** the grace period | New period starts on the payment date |
| Amount below the fee | Rejected |
| Payment date in the future | Rejected |
| Same reference no. used twice for a member | Rejected |
| Payment for a suspended or resigned member | Rejected (reinstate first) |
| Cancelling an older payment while a newer one exists | Rejected (cancel the newest first) |
| Payment submitted or cancelled | Member's paid period, total paid and status are recalculated |

Two payments for the same member submitted at the same moment cannot overlap: the member row is locked
while the period is calculated.

## Data model

```
Membership Type 1 ──< Member 1 ──< Dues Payment (submittable)
                         │
                         └── Customer (ERPNext, optional)
```

## Roles

| Role | Can |
|---|---|
| **Membership Manager** | Everything, including cancelling payments and changing member status |
| **Membership User** | Create members and record or submit payments; cannot cancel or change status |

## Installation

```bash
cd ~/frappe-bench
bench get-app https://github.com/rashidhussainshah/ERPNext_membership --branch main
bench --site <site> install-app membership_dues
```

Optional sample data (never on production):

```bash
bench --site <site> execute membership_dues.demo.create_demo_data
bench --site <site> execute membership_dues.demo.delete_demo_data
```

## REST API

Create an API key and secret for a user (User → Settings → API Access), then:

```bash
# Membership status by email
curl -H "Authorization: token <api_key>:<api_secret>" \
  "https://<site>/api/method/membership_dues.api.get_member_status?email=amina.khan@demo.example.com"

# Record and submit a payment (safe to retry with the same reference_no)
curl -X POST -H "Authorization: token <api_key>:<api_secret>" \
  -H "Content-Type: application/json" \
  -d '{"member": "MEM-2026-00001", "reference_no": "GW-98431", "mode_of_payment": "Online"}' \
  "https://<site>/api/method/membership_dues.api.record_payment"
```

`record_payment` charges the membership type's fee when no `amount` is given. If a payment gateway retries
a request with the same `reference_no`, the existing payment is returned (`"created": false`) and no
duplicate is made.

## Tests

30 integration tests cover the business rules, permissions, the daily job, the API and the ERPNext link.

```bash
# A test site with only Frappe + this app proves it works without ERPNext
bench new-site tests.localhost --install-app membership_dues
bench --site tests.localhost set-config allow_tests true
bench --site tests.localhost run-tests --app membership_dues

# The ERPNext integration tests, on a site that has ERPNext
bench --site <erpnext-site> run-tests --skip-before-tests --module membership_dues.tests.test_erpnext_integration
```

## Development, release and deployment

1. **Develop** on a branch in a local bench with `developer_mode` on. DocType changes made in the UI are
   written to the app's JSON files.
2. **Test**: run the test suite, then check the change by hand in the browser.
3. **Commit and review**: small commits; open a pull request. CI (`.github/workflows/ci.yml`) runs the tests.
4. **Release**: merge to `main`, bump `__version__` in `membership_dues/__init__.py`, tag (`v0.2.0`).
   Changes that need existing data or customizations updated get a patch in `patches.txt`.
5. **Deploy to staging, then production**:
   ```bash
   bench --site <site> backup --with-files
   cd apps/membership_dues && git fetch && git checkout v0.2.0 && cd ../..
   bench --site <site> migrate      # runs new patches and syncs DocTypes
   bench build --app membership_dues
   bench restart                    # production benches (supervisor/systemd)
   ```
6. **Validate after deployment**: open the changed screens, run the report, check `bench --site <site> doctor`
   and the error log. If something is wrong, check out the previous tag, migrate and restart, or restore
   the backup.

## Project structure

```
membership_dues/
├── hooks.py                 install hooks, daily scheduler job
├── api.py                   REST endpoints
├── tasks.py                 daily lapse job
├── install.py               after_install / after_app_install
├── demo.py                  sample data
├── integrations/erpnext.py  optional ERPNext Customer link
├── patches/                 data migrations for existing sites
├── membership_dues/
│   ├── doctype/             membership_type, member, dues_payment
│   └── report/              member_dues_status
└── tests/                   API, scheduler, ERPNext tests and test data helpers
```

## Roadmap

- Create an ERPNext **Sales Invoice** and **Payment Entry** for each dues payment
- Email reminders before a membership expires
- Web portal page where members see their status and pay online
- Workspace with number cards (active, lapsed, collected this month)

## License

MIT
