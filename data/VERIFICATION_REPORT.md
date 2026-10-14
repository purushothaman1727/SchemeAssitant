# Scheme verification report

Checked: 2026-10-13. Dataset: `data/schemes.json`. A rule is `verified` only if its value was read in an official document by the maintainers. Anything else is recorded but never used to produce "does not match".

## Summary

| Status | Count | Schemes |
|---|---|---|
| Verified | 7 | pre-matric-swd, post-matric-swd, top-class-swd, free-coaching-swd, ddrs, udid, sipda |
| Partially verified | 9 | aicte-saksham, adip, national-fund-pwd, pm-kmy, tn-ward-scholarship-welfare-board, tn-unemployment-allowance, tn-high-support-need-assistance, tn-travel-concession, tn-maintenance-allowance |
| Unverified | 4 | ignd-ps, ignoa-ps, ignw-ps, pm-jay |

## Changes from the requested list

| Requested | Finding | Action |
|---|---|---|
| #4 and #5 AICTE Saksham degree / diploma | One scheme covering both degree and diploma (aicte.gov.in) | Merged into `aicte-saksham`; added **Free Coaching Scholarship** (verified in the DEPwD guidelines) to keep 20 |
| #18 Personal Assistance Allowance | No scheme of that name found. Policy Note 2024-25 s.15.2 has "Financial Assistance to DAPs with High Support Need", Rs 1,000/month **to the care taker** | Recorded under the official name |
| #20 Differently Abled Pension Scheme | Could not be verified: cra.tn.gov.in pages unreachable / 404; the Rs 1,000 vs Rs 1,500 amount is contradicted across secondary sources | Replaced with **TN Maintenance Allowance** (Rs 2,000/month, Policy Note s.15.1, verified). DAPS should be re-checked and added when an official page is read |
| #1-3 scholarships | Now components of the *Central Sector Umbrella Scheme Scholarships for Students with Disabilities* | Kept as three entries because their rules differ |
| #7 DDRS | Official page uses both "Disabled" and "Divyangjan" | Both names stored |
| #8 UDID, #9 SIPDA, #7 DDRS | Identity programme / institutional grants, not individual cash benefits | `is_cash_benefit=false`; SIPDA and DDRS gated on `applicant_is_organisation` |

## Source access limitations (not worked around)

| Source | Result |
|---|---|
| scd.tn.gov.in | TLS certificate could not be verified; page not read |
| nsap.nic.in, nsap.gov.in | Host not found |
| nha.gov.in / pmjay.gov.in | Blank page / connection refused |
| pmkisan.gov.in (PM-KMY FAQ and guidelines) | TLS certificate error; figures seen only as search-result quotes |
| myscheme.gov.in | Returned "Something went wrong", no scheme content |
| cra.tn.gov.in/eleg_schemes.php | HTTP 404 (a search result listed it) |
| depwd.gov.in guideline PDFs | Page lists them; the umbrella-guidelines copy was read from a mirror (nitkkr.ac.in). The ADIP revised scheme and National Fund 2026 guidelines were **not** read |

## Per-scheme notes

- **Scholarships (1-3, free coaching):** Read from the OM of 25/09/2024 (sections 2-6, 14). DEPwD lists a later revision notice dated 04/09/2025 that was not read. 40% benchmark disability; Rs 2.5 lakh (pre/post-matric), Rs 8 lakh (top class, free coaching). Slots are capped, so meeting criteria is not an entitlement. NSP notice: AY 2026-27 open from 1 June 2026; this scheme's own deadline was not shown.
- **ADIP:** Revised effective 26/09/2024; approved only until 31/03/2026. Continuation not confirmed. No eligibility rules recorded.
- **NSAP pensions, PM-KMY, PM-JAY:** Figures come from a parliamentary answer and explainer sites. They are stored for transparency but flagged `verified=false`; the engine reports "information unverified".
- **TN Maintenance Allowance:** eligibility is category-based (Table 9): severe 75%+, intellectual disability 40%+, or Parkinson's / spinal cord injury / multiple sclerosis / muscular dystrophy / leprosy-affected at 40%+. It is encoded as a composite rule, and the engine asks for the listed-condition answer when it cannot tell.
- **Tamil Nadu schemes:** Read from the official Policy Note 2024-25 (cms.tn.gov.in). Amounts are for 2024-25 and may have changed. Required documents and application forms are not given in the note.
- **Tamil names:** `name_ta` is intentionally empty; translations must be reviewed by a fluent speaker before publishing.
- **Free Coaching:** an optional note explains that it is coaching for competitive/entrance examinations; the guidelines state no age limit, so none is encoded.
- **accepting_applications:** Unknown (`null`) for every scheme except UDID (portal live). Never show "open" without a notified window.

## To finish verification

1. Re-run the checks from a network that can reach nsap.nic.in, nha.gov.in, pmkisan.gov.in, scd.tn.gov.in.
2. Read the ADIP revised scheme PDF and the National Fund 2026 guidelines; add rules.
3. Read the 04/09/2025 umbrella-scheme revision.
4. Verify TN DAPS on cra.tn.gov.in and add it.
5. Promote rules to `verified=true` only after reading the primary document, via the admin API.
