# BNF code changes

BNF codes can change.  That is: the same presentation might be recorded with different
codes at different points in time.

This directory contains bnf_code_mapping.csv, which is used by the prescribing ingestor
so that prescribing is recorded with the BNF code that would have been used, had a
presentation been prescribed today.  This means that we don't have to worry about
historic BNF codes when querying prescribing data.

bnf_code_mapping.csv is created by the create_bnf_code_mapping command, which processes
the CSV files in the raw/ directory.  Each of these CSV files contains the changes
published in January of a given year.

Changes from 2020 onwards are published by the BSA, and are available here:

* 2020: https://www.nhsbsa.nhs.uk/bnf-code-changes
* 2021: https://www.nhsbsa.nhs.uk/bnf-code-changes-january-2021
* 2022: https://www.nhsbsa.nhs.uk/bnf-code-changes-january-2022
* 2023: https://www.nhsbsa.nhs.uk/bnf-code-changes-january-2023
* 2024: https://www.nhsbsa.nhs.uk/bnf-code-changes-january-2024
* 2025: https://www.nhsbsa.nhs.uk/bnf-version-changes-january-2025
* 2026: https://www.nhsbsa.nhs.uk/bnf-version-changes-january-2026

The changes are published in spreadsheets in a slightly different form each year, so we
cannot automate creating the CSV files.

Changes from before 2020 was sent to the OpenPrescribing team via email, and are checked
in to openprescribing codebase here:

https://github.com/bennettoxford/openprescribing/tree/main/openprescribing/frontend/management/commands/presentation_replacements

We currently use prescribing data going back to 2014, and so we use the mappings from
January 2015 onwards.  There is earlier prescribing data going back to 2010, and if we
use this, we should bring in earlier mappings too.

Note that some changes were erroneously published.  Those changes have been removed from
the CSV files.  See openprescribing#4876 for some background.  Additionally, the 2015
changes include some changes at other levels of the BNF hierarchy (eg chemicals).  These
correspond to presentations that have not been prescribed since before 2014, and so thse
have been removed from 2015.csv.  These changes are reflected in the git history.
