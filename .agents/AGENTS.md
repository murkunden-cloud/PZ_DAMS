# Data Fetching Rule
- The program is currently primarily for view and report purposes and is not fully automated.
- The user manually edits the master file (origional_35_dc.xlsx) every month.
- Any future changes to the caching or data loading mechanisms MUST ensure that these manual updates take effect automatically in network mode (i.e., the cache must be strictly invalidated upon file modification so the web dashboard always reflects the newest data).

# Employee Master Data & Pay Group Rule
- When importing employee data from master_employe.xlsx into the database (e.g., via migrate_employees.py), the paygrp column must be read accurately. It contains values 1, 2, 3, 4. Do not override or default these values improperly.
- The pay_group determines the scope / bifurcation of cases: Pay Group I and II (1 and 2) are 'Statewise', whereas Pay Group III and IV (3 and 4) are 'Circlewise'. 
- For UI view generation and pendency/report counts (e.g., in DC_PendencyEngine.py), ALWAYS rely on the pay_group column data mapped to individual cases rather than attempting to parse layout-specific marker rows ('circle wise', 'state wise') from legacy spreadsheets.


# Data Extraction & Migration Rule
- ALWAYS ensure that data extraction scripts (e.g. \migrate_cases.py\) scan all rows starting from index 0 (\start_row = 0\). Do NOT rely on hardcoded \data_start\ indexes from metadata to skip header rows, because users frequently type data above the expected start lines. Instead, rely natively on the \has_cpf_value\ validator to filter out header rows dynamically. This ensures no valid cases are ever skipped.
- THUMB RULE FOR COUNTING: Only use specific active sheets for counting. Minor cases strictly rely on 6DC. Suspension cases strictly rely on 12DC and 13DC (ignore 14DC/15DC). Major cases strictly rely on 22DC and 23DC.



# Database vs Excel Source of Truth Rule
- The primary source of truth for all view generation, matching, and reporting is the manually edited Excel master files (origional_35_dc.xlsx and master_employe.xlsx), loaded via DC_DataLoader.
- Do NOT implement features or reports (e.g., Unmatched CPF Errors) by running raw SQL queries directly against the PostgreSQL or SQLite database (DC_DatabaseManager), as the database acts primarily as an archive and might be out of sync with the Excel files. 
- Always rely on loader.load_all() and loader.load_emp() when iterating over case data for active application logic to prevent schema mismatch errors and stale data.
