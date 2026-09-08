<div align="center">

<img src="https://img.shields.io/badge/Jodo-Business%20Operations%20Platform-2E7BF6?style=for-the-badge&labelColor=0B1120" />
<br/><br/>
<img src="https://img.shields.io/badge/Python-Flask-0FBCB0?style=flat-square&logo=flask&logoColor=white&labelColor=0F1929" />
<img src="https://img.shields.io/badge/Frontend-HTML%20%2F%20CSS%20%2F%20JS-2E7BF6?style=flat-square&labelColor=0F1929" />
<img src="https://img.shields.io/badge/ERP-Odoo%20XML--RPC-0FBCB0?style=flat-square&labelColor=0F1929" />
<img src="https://img.shields.io/badge/AI-Agent%20Enabled-F59E0B?style=flat-square&labelColor=0F1929" />
<img src="https://img.shields.io/badge/Status-In%20Development-7B93B8?style=flat-square&labelColor=0F1929" />

<br/><br/>

<img src="JodooLogo.png" alt="Jodo Logo" />

### Not just another ERP dashboard.
### A role-specific, AI-assisted, fully customisable operations platform — built for every kind of business.

<br/>

</div>

---

## The Problem with Odoo (and every ERP like it)

```
┌───────────────────────────────────────────────────────────────────[...]
│                  ODOO — full admin interface                      │
│                                                                  │
│  CRM │ Sales │ Accounting │ HR │ Manufacturing │ Helpdesk │ ...  │
│                                                                  │
│         ↕  every user, every role, sees ALL of this  ↕          │
│                                                                  │
│  Inventory │ Transfers │ Payroll │ POS │ Marketing │ Repairs ... │
└───────────────────────────────────────────────────────────────────[...]

  A warehouse worker. A retail manager. A restaurant owner.
  A freelance agency. All given the same cluttered interface.
  All forced to navigate what they don't need to reach what they do.

                           ↓  Jodo fixes this  ↓

┌──────────────┬───────────────────┬────────────────────────────────[...]
│  Your role   │  Your dashboards  │  Your data — nothing extra   │
│  Your layout │  Your AI agent    │  Connected. Clean. Fast.     │
└──────────────┴───────────────────┴────────────────────────────────[...]
```

---

##  Who Is Jodo For?

```
                            ┌─────────────┐
                            │    JODO     │
                            │  Platform   │
                            └──────┬──────┘
           ┌──────────────┬────────┼────────┬──────────────┐
           ▼              ▼        ▼         ▼              ▼
    ┌────────────┐ ┌──────────┐ ┌──────┐ ┌──────────┐ ┌──────────┐
    │ Warehouse  │ │  Retail  │ │ Cafe │ │ Agency / │ │  Any SME │
    │ & Logistics│ │  Store   │ │  &   │ │Freelance │ │ that runs│
    │            │ │ Manager  │ │ Food │ │  Team    │ │ on Odoo  │
    └────────────┘ └──────────┘ └──────┘ └──────────┘ └──────────┘
    Stock levels   Sales today  Orders   Project       Custom
    Transfers      Inventory    Kitchen  pipeline      role view
    Reorder alerts POS summary  Staffing Invoices      AI agent
```

Each business type gets its own configured dashboard. No two Jodo setups need to look the same.

---

## Core Features

### 1 — Customisable Dashboards

```
┌─────────────────────────────────────────────────┐
│  Jodo Dashboard Builder                         │
│                                                 │
│  [ Stock Panel  ▓▓▓▓▓▓▓▓░░ ]  [ + Add panel ]  │
│  [ Transfers    ▓▓▓▓░░░░░░ ]                    │
│  [ Alerts       ▓▓▓▓▓▓░░░░ ]  drag to reorder  │
│                                                 │
│  Role: Warehouse Manager ▾                      │
│  Saved layouts: Morning view / Dispatch view    │
└─────────────────────────────────────────────────┘
```

Users can add, remove, and reorder panels. Layouts save per role and per user. A warehouse manager's morning view looks nothing like an accountant's closing view — and both are built from the same p[...]

---

### 2 — Team Networking (Discord-style)

```
┌─────────────────────────────────────────────┐
│  Jodo Workspace                             │
│                                             │
│  # general          ● Ravi (Warehouse)      │
│  # dispatch-alerts  ● Priya (Accounts)      │
│  # low-stock-watch  ○ Arjun (offline)       │
│                                             │
│  [ ALERT] Corner Protectors — 5 units    │
│  Ravi: on it, reorder submitted             │
│  Priya: invoice raised ✓                   │
│                                             │
│  [ type a message...              ] [send]  │
└─────────────────────────────────────────────┘
```

Persistent, role-aware team channels embedded directly in the platform. Alerts from the dashboard post automatically into the relevant channel. No switching between Slack, WhatsApp, and the ERP.

---

### 3 — AI Operations Agent

```
┌──────────────────────────────────────────────┐
│  Jodo AI Agent                               │
│                                              │
│  You: "Which products are going to run out   │
│         before Friday based on current       │
│         transfer volume?"                    │
│                                              │
│  Agent: Based on today's pending transfers,  │
│  Corner Protectors (5 units, 3 outgoing)     │
│  and Air Pillows (0 units) will hit zero     │
│  before Friday. Shall I raise a reorder?     │
│                                              │
│  [ Yes, raise reorder ] [ Show me the data ] │
└──────────────────────────────────────────────┘
```

The AI agent reads live dashboard data and answers natural language questions about operations. It can flag patterns, suggest reorders, and summarise daily status — without the user building a singl[...]

---



##  Get Running in 60 Seconds

```bash
# Clone
git clone https://github.com/your-org/jodo.git && cd jodo

# Virtual environment
python -m venv venv && source venv/bin/activate

# Install
pip install -r requirements.txt

# Run
python app.py
```

Open **`http://localhost:5000`**

---

##  Team

Members: Krina, Vaibhavi, Prachi, Triesha, Aayoshi  

---

##  References

- Odoo. (2025). *XML-RPC external API.* https://www.odoo.com/documentation/17.0/developer/reference/external_api.html
- G2. (2026). *Odoo ERP reviews.* https://www.g2.com/products/odoo-odoo-erp/reviews
- Trustpilot. (2026). *Odoo reviews.* https://www.trustpilot.com/review/odoo.com

---

<div align="center">
<sub>Built on Odoo · Simplified for every role · Course project — Digital Business Systems</sub>
</div>
