# DC Manager - Disciplinary Cases Management System for Pune Zone

## Quick Start

```bash
cd D:\MYPRO\DC\DC_Manager
python DC_Manager.py
```

This now starts the offline local web app at:

```text
http://127.0.0.1:5000/
```

For the terminal menu instead:

```bash
python DC_Manager.py --cli
```

## What This Does

Manages your 35-sheet DC (Disciplinary Cases) Excel workbook with:
- **Auto-extract DC numbers** from long dispatch references (e.g. `SE/PRC/HRD/CONF/1450/2023/1060` → `1060`)
- **Add/Edit/Delete** records in any sheet
- **Employee search** by CPF number (full case history) or name
- **Pendency reports** (Zone/Circle/Division wise)
- **HTML Dashboard** - opens in browser with charts
- **Auto-backup** before every change
- **Closed cases archive** (separate from source Excel)

## File Structure

```
D:\MYPRO\DC\
  origional_35_dc.xlsx     ← Your DC data (DO NOT RENAME)
  master_employees.xlsx    ← Employee master data
  DC_Manager\
    DC_Manager.py         ← Main program (run this)
    DC_Dashboard.html     ← Generated dashboard (auto-created)
  backups\                 ← Automatic backups
  cache\                   ← Temporary cache files
  closed_cases_db.json     ← Closed cases archive
```

## Data File Location

- The app auto-detects `origional_35_dc.xlsx` and `master_employees.xlsx` from:
  - `DC_MANAGER_DATA_DIR` if you set it
  - the parent folder of `DC_Manager.py`
  - the project folder itself
- Runtime files now stay inside `DC_Manager\runtime\`:
  - `runtime\backups\`
  - `runtime\cache\`
  - `runtime\closed_cases_db.json`

## Menu Options

| # | Feature | What it does |
|---|---------|-------------|
| 1 | View Sheet Structure | Shows column headers for any sheet |
| 2 | Add New Record | Add a new case to any DC sheet |
| 3 | Edit Record | Update existing record by CPF |
| 4 | Delete Record | Remove a record (with backup) |
| 5 | **Extract DC Numbers** | Auto-extract DC# from dispatch refs |
| 6 | Search by CPF | Full history for one employee |
| 7 | Search by Name | Find employees by name |
| 8 | Pendency Summary | Zone/Circle/Division report |
| 9 | HTML Dashboard | Visual dashboard in browser |
| 10 | Closed Cases | View archived closed cases |
| 11 | Mark Closed | Archive a case as closed |
| 12 | Manual Backup | Create backup on demand |
| 13 | List Backups | View all previous backups |

## CLI Commands

```bash
# Offline web app
python DC_Manager.py

# Terminal menu
python DC_Manager.py --cli

# Extract DC numbers from all sheets
python DC_Manager.py --extract

# Show pendency summary as JSON
python DC_Manager.py --pendency

# View sheet column structure
python DC_Manager.py --structure 6DC

# Find employee by CPF in a sheet
python DC_Manager.py --find 6DC 2208334

# Export reports
python DC_Manager.py --export-csv
python DC_Manager.py --export-json
```

## Module Structure

- `DC_DataLoader.py` - workbook reading, cache, master employee handling, DC extraction helpers
- `DC_Editor.py` - add/edit/delete/extract/archive operations
- `DC_PendencyEngine.py` - pendency calculation and org summaries
- `DC_Dashboard.py` - dashboard data and chart helpers
- `DC_BackupManager.py` - versioned auto-backups
- `DC_MainApp.py` - terminal admin menu
- `DC_Reports.py` - pendency export files
- `DC_WebApp.py` - offline one-page Flask web app

## Sheet Reference

### Minor DC
| Sheet | Description | Scope |
|-------|-------------|-------|
| 4DC | Minor DC Initiated | Statewise (Class I/II) |
| 5DC | Minor DC Initiated | Circlewise (Class III/IV) |
| 6DC | **Consolidated Minor DC (4DC+5DC)** | All |
| 7DC | Minor DC Closed | Statewise |
| 8DC | Minor DC Closed | Circlewise |

### Suspension
| Sheet | Description | Scope |
|-------|-------------|-------|
| 12DC | Suspended end of last month | Statewise |
| 13DC | Suspended end of last month | Circlewise |
| 14DC | Suspended current month | Statewise |
| 15DC | Suspended current month | Circlewise |
| 16DC | Suspension Revoked | Statewise |
| 17DC | Suspension Revoked | Circlewise |

### Major DC
| Sheet | Description | Scope |
|-------|-------------|-------|
| 20DC | Chargesheet Initiated (current month) | Statewise |
| 21DC | Chargesheet Initiated (current month) | Circlewise |
| 22DC | **All Major Cases (upto current month)** | Statewise |
| 23DC | **All Major Cases (upto current month)** | Circlewise |
| 24DC | Finalised Cases | Statewise |
| 25DC | Finalised Cases | Circlewise |

### Appeals
| Sheet | Description | Scope |
|-------|-------------|-------|
| 29DC | Appeals Disposed | Statewise |
| 30DC | Appeals Disposed | Circlewise |

## Adding a New Record (Example)

```
Sheet name: 6DC
col=values to enter:
2=Rahul Kumar Sharma
3=2200123
4=I
5=30.09.2035
6=Pune Circle Office
7=Other
8=NA
9=SE/PRC/HRD/CONF/1450/2023/1060
10=
11=Warning issued
12=Pending
```

## Key Columns

- **CPF No**: Column C (index 3) in most sheets
- **Dispatch/DC Ref**: Column I (index 9) in most sheets - DC# is auto-extracted from this
- **Chargesheet#**: Column J (index 10) for Major DC sheets

## Closed Cases Archive

Cases marked as closed via option 11 are stored in `closed_cases_db.json` (separate from your source Excel). This is because your current Excel does NOT store closed case data.

## Auto-Backup

Every time you Add, Edit, or Delete a record, an automatic backup is created in `D:\MYPRO\DC\backups\`. Backups are also listed in `manifest.json`.

## Requirements

- Python 3.9+
- `pip install openpyxl pandas` (the program will prompt if missing)

## Notes

- The program reads from `origional_35_dc.xlsx` - do not rename this file
- Cache files in `cache\` are temporary and rebuilt automatically
- The HTML dashboard is static (regenerate with option 9 after updates)
