"""Generate a deterministic, synthetic SAP support dataset for the POC.

Writes data/team.csv, data/history.csv and data/new_tickets.csv.
Replace these files with your own (anonymized) exports to run on real data.
"""
from __future__ import annotations

import csv
import random
from datetime import date, timedelta
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
TODAY = date(2026, 11, 1)

TEAM = [
    # id, name, seniority (1=junior..4=lead), status, open, max_open, skills
    ("E01", "Ravi", 4, "active", 5, 8, "FI:4;CO:3"),
    ("E02", "Anita", 3, "active", 3, 8, "MM:4;SD:2"),
    ("E03", "Karan", 2, "active", 6, 8, "SD:3;MM:2"),
    ("E04", "Meera", 1, "active", 1, 6, "FI:2;CO:1"),
    ("E05", "Joseph", 3, "leave", 0, 8, "BASIS:4;ABAP:2"),
    ("E06", "Priya", 2, "active", 2, 8, "ABAP:3;BASIS:2"),
    ("E07", "Sameer", 3, "left", 0, 8, "PP:4;MM:3"),
    ("E08", "Divya", 2, "active", 4, 8, "PP:3;CO:2"),
    ("E09", "Arjun", 1, "active", 2, 6, "BASIS:2;SD:1"),
]

# module -> list of (title, description, type, complexity, resolution)
TEMPLATES = {
    "FI": [
        ("Payment run F110 not picking vendor invoices", "Automatic payment program F110 skips open items for vendor {n}. Payment method in vendor master looks correct.", "incident", "medium", "Payment block on invoices removed; house bank ranking order corrected in FBZP."),
        ("GL posting error in FB50", "User gets error 'Balance in transaction currency' while posting GL document in company code {cc}.", "incident", "low", "Explained balancing; tax code missing on line item."),
        ("Vendor invoice FB60 tax calculation wrong", "Tax amount on vendor invoice in FB60 is calculated incorrectly for tax code V{n}.", "incident", "medium", "Tax condition record in FTXP corrected."),
        ("Period closing: posting period not open", "Accounting period {n} is closed, users cannot post invoices. OB52 change required.", "service_request", "low", "Opened period in OB52 after finance approval."),
        ("Asset depreciation run AFAB failing", "Depreciation run AFAB terminates with errors for asset class {n} in production.", "incident", "high", "Inconsistent asset values repaired; depreciation key fixed and run repeated."),
    ],
    "CO": [
        ("Cost center not found in KS03", "Cost center {n} is missing for controlling area {cc}; postings fail.", "incident", "low", "Cost center validity date extended."),
        ("Internal order settlement KO88 error", "Settlement of internal order {n} fails with missing settlement rule.", "incident", "medium", "Settlement rule maintained in KO02."),
        ("Profit center assignment wrong on postings", "Postings for material {n} go to dummy profit center.", "incident", "medium", "Profit center assignment in material master corrected."),
    ],
    "MM": [
        ("Goods receipt MIGO error for PO", "MIGO goods receipt for purchase order 45000{n} fails: 'Deficit of stock'.", "incident", "medium", "Stock posted via 561 after inventory check; GR repeated."),
        ("Purchase order ME21N release strategy not triggered", "PO created in ME21N does not trigger release strategy for value above {n}k.", "incident", "high", "Classification characteristics for release strategy corrected in CL20N."),
        ("Material master extension to new plant", "Extend material {n} to plant {cc} via MM01.", "service_request", "low", "Material extended to plant views."),
        ("Invoice verification MIRO price variance block", "MIRO invoice for PO {n} blocked due to price variance.", "incident", "medium", "Tolerance key reviewed; invoice released in MRBR."),
    ],
    "SD": [
        ("Sales order VA01 pricing condition missing", "Pricing condition PR00 not determined in sales order for customer {n}.", "incident", "medium", "Condition record created in VK11; access sequence verified."),
        ("Billing document VF01 not created", "Delivery {n} not relevant for billing; VF01 gives error.", "incident", "medium", "Item category billing relevance corrected in copy control."),
        ("Output type not printing invoice", "Invoice output for billing {n} not printed, NACE output determination issue.", "incident", "low", "Output condition record maintained."),
        ("Credit block on sales order", "Sales order {n} blocked by credit management, customer needs release.", "service_request", "low", "Released in VKM3 after approval."),
    ],
    "PP": [
        ("MRP run MD01 not generating planned orders", "MRP run for plant {cc} does not create planned orders for material {n}.", "incident", "high", "MRP type and lot size corrected in MRP views."),
        ("Production order CO01 BOM explosion error", "Production order cannot be created; BOM {n} not found for production version.", "incident", "medium", "Production version maintained in C223."),
        ("Confirmation CO11N backflush failing", "Backflush of components fails during confirmation of order {n}.", "incident", "medium", "Storage location for backflush maintained."),
    ],
    "BASIS": [
        ("Transport request stuck in STMS import", "Transport {n} stuck in import queue to production system.", "incident", "medium", "tp import restarted; RDDIMPDP job rescheduled."),
        ("User locked, password reset SU01", "User {n} locked after wrong password attempts, needs reset.", "service_request", "low", "Password reset in SU01."),
        ("Background job SM37 cancelled", "Nightly background job {n} cancelled with memory issue.", "incident", "medium", "Job variant split; memory parameters adjusted."),
        ("System performance slow for all users", "Production system response times very slow for all users since morning, ST03 shows high DB time.", "incident", "high", "Expensive SQL identified and index created; stats updated."),
        ("Authorization missing for transaction", "User {n} gets 'no authorization' for transaction; SU53 attached.", "service_request", "low", "Role adjusted in PFCG."),
    ],
    "ABAP": [
        ("Short dump ST22 in custom Z report", "Custom report ZFI_{n} terminates with short dump TSV_TNEW_PAGE_ALLOC_FAILED.", "incident", "high", "Internal table processing rewritten with package size."),
        ("Smartform layout change for invoice", "Change logo and footer in invoice smartform Z_INV_{n}.", "change", "low", "Smartform updated and transported."),
        ("BAdI enhancement not triggered", "Custom BAdI implementation for {n} not called during save.", "incident", "medium", "Filter values of BAdI implementation corrected."),
        ("New ALV report for open items", "Create new ALV report listing open items by vendor for company code {cc}.", "change", "medium", "Report ZALV_{n} developed and transported."),
    ],
}

# Who historically resolves what (weights). Includes people now on leave / left.
RESOLVERS = {
    "FI": {"E01": 6, "E04": 3},
    "CO": {"E01": 3, "E08": 3, "E04": 1},
    "MM": {"E02": 6, "E03": 2, "E07": 2},
    "SD": {"E03": 5, "E02": 2, "E09": 1},
    "PP": {"E07": 5, "E08": 4},
    "BASIS": {"E05": 6, "E09": 3, "E06": 2},
    "ABAP": {"E06": 5, "E05": 2},
}

PRIORITY_BY_COMPLEXITY = {"low": ["P4", "P3"], "medium": ["P3", "P2"], "high": ["P2", "P1"]}
HOURS = {"low": (1, 6), "medium": (4, 24), "high": (16, 72)}


def main() -> None:
    rng = random.Random(42)
    DATA.mkdir(exist_ok=True)

    with open(DATA / "team.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "name", "seniority", "status", "open_tickets", "max_open", "skills"])
        w.writerows(TEAM)

    rows = []
    for i in range(240):
        module = rng.choice(list(TEMPLATES))
        title, desc, ttype, cx, res = rng.choice(TEMPLATES[module])
        fill = {"n": rng.randint(100, 999), "cc": rng.choice(["1000", "2000", "3000"])}
        people = RESOLVERS[module]
        resolver = rng.choices(list(people), weights=list(people.values()))[0]
        created = TODAY - timedelta(days=rng.randint(5, 365))
        lo, hi = HOURS[cx]
        rows.append({
            "ticket_id": "",
            "created": created.isoformat(),
            "title": title.format(**fill),
            "description": desc.format(**fill),
            "module": module,
            "type": ttype,
            "complexity": cx,
            "priority": rng.choice(PRIORITY_BY_COMPLEXITY[cx]),
            "resolver_id": resolver,
            "hours_to_resolve": rng.randint(lo, hi),
            "resolution_notes": res,
        })
    rows.sort(key=lambda r: r["created"])
    for i, r in enumerate(rows, 1):
        r["ticket_id"] = f"INC{i:05d}"

    with open(DATA / "history.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    new = [
        ("NEW001", "F110 payment proposal missing vendor items", "Payment run proposal does not include open invoices for vendor 4711 although due date passed.", "P2"),
        ("NEW002", "MIGO error deficit of stock", "Goods receipt against purchase order 4500012 fails with deficit of stock in plant 2000.", "P3"),
        ("NEW003", "Production system extremely slow", "All users report slow response in production since 9am, transactions time out.", "P1"),
        ("NEW004", "Planned orders not created after MRP", "MD01 run completed but no planned orders for finished goods in plant 1000.", "P2"),
        ("NEW005", "Need access to VA02", "User needs authorization to change sales orders, SU53 screenshot attached.", "P4"),
        ("NEW006", "Dump in Z report memory", "Custom Z report dumps with TSV_TNEW_PAGE_ALLOC_FAILED when run for full year.", "P2"),
    ]
    with open(DATA / "new_tickets.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["ticket_id", "title", "description", "priority"])
        w.writerows(new)

    print(f"Wrote {len(TEAM)} team members, {len(rows)} history tickets, {len(new)} new tickets to {DATA}")


if __name__ == "__main__":
    main()
