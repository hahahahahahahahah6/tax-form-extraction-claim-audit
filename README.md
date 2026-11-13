# Documentation claim auditor

An offline audit tool comparing documentation promises against listed call patterns in Python source. Inspected code is parsed, never imported or executed. No runtime dependencies, network calls, telemetry, or output files are involved.

## Install and run

Requires Python 3.9 or newer.

```sh
python3 -m pip install .
tax-form-extraction-claim-audit --version
tax-form-extraction-claim-audit audit /path/to/repo --json
python3 -m tax_form_extraction_claim_audit audit . --verbose
tax-form-extraction-claim-audit audit . --ignore tests --ignore vendor --fail-on medium
python3 -m unittest discover
```

The repository defaults to the current directory. Each repeatable ignore option accepts one relative path prefix and matches whole path components. The threshold accepts lowercase high (default) or medium. Exit codes are 0 below the threshold, 2 for findings at or above it, and 1 for usage or I/O errors. Version output is 0.1.0. A FAIL verdict can exit 0 when all findings fall below the threshold.

JSON contains verdict, findings, production_evidence and test_evidence. Each finding contains id, severity, message and docs. Positive promises without production evidence receive HIGH, or MEDIUM when evidence exists only in tests. Denials contradicted by production evidence receive HIGH. With no source files a positive promise fails and a denial passes. Each family produces at most one finding.

```text
documented-tax-form-extraction-claim-false
documented-no-tax-form-extraction-claim-false
```

## Scope

Documentation includes root README.md and Markdown files with a docs path component. Backtick and tilde fenced blocks with up to three leading spaces are excluded; inline code counts. Paragraphs split on blank lines. Matching lowercases text, expands contractions, replaces hyphens with spaces and collapses whitespace. Exact phrases match at word boundaries, longest first with alphabetical ties. Denial spans are removed before positive matching. The phrase module contains the fixed vocabulary.

Source is inspected with the standard syntax tree parser. Symlinked files and directories are skipped. Source under fixtures, docs and examples supplies no evidence. Files under tests or with the conventional test prefix or suffix count separately. Invalid syntax supplies no evidence. Each paired route must occur in one module. Import aliases are resolved; assignments, annotated assignments and context manager bindings are tracked. Local functions, methods and classes shadow matching route names.

```text
Azure: DocumentAnalysisClient / DocumentIntelligenceClient construction
 import azure.ai.formrecognizer / azure.ai.documentintelligence
 begin_analyze_document / begin_analyze_document_from_url
 first positional literal or model_id keyword literal in the exact 48-id list
Veryfi: Client construction + process_w2_document / process_w2_document_url /
 process_w9_document / process_w9_document_url /
 process_w8_document / process_w8_document_url
Generic: 24 exact names in phrases.py; attribute calls or imported name calls
Mindee: no route, with ANY product
```

## Limits

Static pattern matching is not semantic judgement. Dead code counts; untraceable alias chains are missed. Exact phrases only, with denial handling limited to the listed phrases. Every paired route must sit in a single module. Azure Document Intelligence and Veryfi are cloud APIs: source calls establish neither configured credentials nor successful execution.

Broad wording may describe generating blank templates, downloading blank forms, or filing them. Return wording can describe a computed function result rather than an IRS document. W2 can mean a second weight matrix in machine learning. The number 1099 can mean an item count or the Java RMI registry port. These meanings can cause false positives. The tool flags wording and uses listed code patterns to decide.

```text
Ambiguous phrases:
tax form extraction / extract tax form / extract tax forms
tax return extraction / extract tax returns
w 2 extraction / w2 extraction / extract w 2 forms
1099 extraction / extract 1099 forms
```

Generic calls may compute a tax value or parse numbers typed by a user; listed calls still count subject to shadowing. Parsing an already extracted W-2 string alone is missed. Handwritten regular expressions over OCR text with manual field assembly are missed unless a listed call occurs. A thin wrapper containing only subprocess calls supplies no evidence, including the Veryfi CLI, Mindee CLI, or any external CLI.

```text
extract_tax_return / parse_tax_return / extract_w2 / parse_1099
re.search / re.findall
subprocess: veryfi w2s process; mindee CLI
```

Veryfi generic processing handles receipts and invoices. Check operations and bank statement operations belong to separate document families. Retrieval and management of already processed forms do not establish the checked operation. Only the listed W-2, W-9 and W-8 processing calls count.

```text
Veryfi excluded:
process_document / process_document_url
process_check / process_check_url / process_check_with_remittance /
process_check_with_remittance_url
process_bank_statement_document / process_bank_statement_document_url
classify_document
get_w2s / get_w2 / delete_w2 / get_w9s / get_w9 / delete_w9 /
get_w8s / get_w8 / delete_w8
```

Azure requires exact case-sensitive v4.0 model IDs. The unified model includes the regional suffix. Bare and truncated spellings do not count. Other models cover invoices, receipts, layouts, plain text, ID documents, checks, pay stubs and bank statements.

```text
Counts: prebuilt-tax.us, prebuilt-tax.us.W-4, prebuilt-tax.us.w2
Does not count: prebuilt-tax, prebuilt-tax.us.w, prebuilt-tax.us.1099,
 prebuilt-tax.us.w-4
Other excluded models: prebuilt-invoice / prebuilt-receipt / prebuilt-layout /
 prebuilt-read / prebuilt-idDocument / prebuilt-check.us / prebuilt-payStub.us /
 prebuilt-bankStatement.us
```

Mindee has no fixed product for the checked capability in its Python SDK, verified against wheel 4.22.0 on 2026-11-13. Its Tax Return OCR offering uses a custom workflow. The generic Tax field class is reused inside other products and supplies no evidence. Every product passed to its parse method is excluded. Textract has no operation for the checked document type; generic document and expense analysis do not count.

```text
Mindee parse: ANY product, including BankCheckV1, InvoiceV4, ReceiptV5,
 PassportV1, FinancialDocumentV1, BankAccountDetailsV2, CustomV1
Textract: analyze_document / analyze_expense /
 start_document_analysis / get_expense_analysis
```

Plain text, OCR, CSV, spreadsheet and table operations alone do not count. Bare imports, strings, comments, bare references, invalid syntax and evidence split between modules do not count.

```text
pdfplumber / fitz / pypdf / PyPDF2 / pdfminer: extract_text
pytesseract: image_to_string; pandas: read_csv / read_excel
camelot: read_pdf; tabula: read_pdf / convert_into
pdfplumber: extract_table / extract_tables / find_table / find_tables
fitz: find_tables
```

Specific W-4, 1095A, 1095C and 1098 wording is outside the phrase lists; generic wording can cover those forms. Both W2 plural spellings below are included. The short 1040 plural is excluded; only the two listed 1040 phrases count. Adjacent document types and filing, preparation or calculation promises are outside this family's phrase lists.

```text
Excluded: extract w 4 forms / extract 1095a forms / extract 1098 forms
Included: extract w2s / extract w 2s
Excluded: extract 1040s
Included: 1040 extraction / extract 1040 forms
Excluded adjacent phrases:
extract invoices / invoice extraction; extract receipts / receipt extraction
extract passports / passport extraction / ID document extraction
extract bank checks / check extraction
extract bank statements / statement extraction
file taxes / calculate tax / prepare tax returns
```

MIT licensed.
