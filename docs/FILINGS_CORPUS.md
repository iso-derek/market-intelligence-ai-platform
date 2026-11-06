# Bounded filings corpus

D4.1 creates a small, immutable local corpus for later retrieval and question-answering evaluation. It does not claim live filings ingestion or RAG.

## Corpus boundary

The corpus contains three fictional repository-authored annual reports for Alpha Industries, Beta Retail, and Gamma Software. Each report has three explicit pages and two titled sections per page. The amounts reconcile with the D2 fundamental fixtures, including Alpha's complete restated report.

The reports are educational data. They are not SEC, Companies House, exchange, issuer, or licensed vendor filings.

## Manifest and integrity

`data/filings/manifest.csv` records:

- stable document ID and file name;
- company and ticker;
- report form and fiscal period end;
- filing and substantiated availability timestamps;
- repository source URI;
- expected SHA-256 of the exact UTF-8 bytes.

Loading fails if a file escapes the corpus root, is missing, exceeds 2 MB, contains null bytes, is not UTF-8, or does not match its manifest hash. Document IDs and names must be unique.

## Page and section parsing

Every report uses explicit `=== PAGE n ===` markers and `## Section` headings. Page numbers must be consecutive from one. The parser emits one passage per section with:

- document and passage IDs;
- page and section position;
- fiscal period, filing time, and availability time;
- company, ticker, form, source URI, and document hash;
- normalized text and its own SHA-256.

The passage hash identifies normalized section text; the document hash identifies the original bytes. They answer different reproducibility questions.

## Point-in-time rule

A historical view includes a report only when `available_at <= cutoff`. Its passages are included or excluded as a complete document. The 23 January view contains Beta only; the 1 February view adds Gamma; the 1 March view includes Alpha's later restated report.

## Security and limitations

- The parser accepts only bounded local UTF-8 text with a fixed grammar.
- It does not execute macros, scripts, HTML, embedded links, or document instructions.
- It does not parse arbitrary PDFs, OCR, tables, footnotes, or exhibits.
- It does not fetch remote filings or establish redistribution rights.
- Search, embedding retrieval, grounded QA, and semantic support evaluation are not implemented in D4.1.
