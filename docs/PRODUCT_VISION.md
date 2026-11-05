# Product vision — Market Intelligence AI Platform

## Objective

Build a high-quality, source-grounded financial research and market-intelligence application that demonstrates financial analysis, business analytics, NLP, machine learning, quantitative research, and disciplined software engineering.

This is the complete target state. It is not an implemented-feature list. The current verified scope is maintained in `DEVELOPMENT_STATUS.md`, and delivery order is maintained in `ROADMAP.md`.

## Target capabilities

### 1. Financial market intelligence

- Equities, indices, currencies, commodities, and sectors.
- Historical and latest available data with explicit timestamps.
- Trends, volatility, and comparative performance.
- Interactive, explainable market views.

### 2. Macroeconomic intelligence

- GDP, CPI, PPI, PMI, employment, inflation, and policy rates.
- Central-bank decisions and interest-rate developments.
- Economic calendars and event monitoring.
- Point-in-time relationships between macro releases and markets, including revisions.

### 3. Financial news and sentiment

- Licensed news collection, categorisation, and provenance.
- Evaluated financial sentiment analysis.
- Named-entity recognition and entity resolution.
- Event detection, relevance scoring, and company/sector links.

### 4. Specialised research agents

- Company Research Agent.
- Macroeconomic Research Agent.
- Financial News Agent.
- Market Risk Agent.
- Research Synthesis Agent.

Each agent must have a bounded responsibility, typed tools, traceable evidence, cost/time limits, and measurable evaluation. Agents must not invent figures or replace tested financial calculations.

### 5. Retrieval-augmented generation

- Appropriately licensed company filings and reports.
- Parsing, document identity, chunking, and metadata.
- Lexical and vector retrieval baselines.
- Source-grounded question answering with citations and abstention.
- Retrieval-quality, answer-correctness, numerical-consistency, and faithfulness evaluation.

### 6. Company and fundamental analysis

- Profiles and normalised financial statements.
- Revenue, earnings, profitability, balance-sheet, and cash-flow analysis.
- Financial ratios and valuation metrics with worked definitions.
- Peers, competitors, and historical earnings context.

### 7. Market-impact modelling

- Event studies for news and economic releases.
- Carefully designed sentiment/event features.
- Historical reactions and transparent predictive comparisons where justified.
- Point-in-time safeguards, uncertainty estimates, and honest negative results.

### 8. Fixed income and foreign exchange

- Government and corporate yields, curves, and movements.
- Credit spreads with explicit reference instruments.
- FX monitoring with clear quote direction and currency units.
- Relationships among rates, currencies, and economic conditions.

### 9. Automated investment research

- Evidence-backed company reports and market briefings.
- Economic summaries, theses, risks, scenarios, and uncertainties.
- Exportable reports whose claims and calculations reconcile to their sources.

### 10. Financial knowledge graph

- Time-aware relationships among companies, sectors, instruments, and events.
- Evidence-backed entity and relationship extraction.
- Inspectable network views and graph-supported research.
- Evaluation against simpler retrieval approaches before graph complexity is retained.

### 11. Professional experience

- Company and market search.
- Dedicated evidence, market, macro, company, risk, and research pages.
- Clear freshness, source, unit, loading, and error states.
- Responsive and accessible interaction.

### 12. Automation, engineering, and cloud

- Reliable, idempotent ingestion pipelines.
- SQL or another justified structured store.
- Scheduled processing only after manual replay is reliable.
- Automated tests, CI, secure configuration, monitoring, recovery, and cost controls.
- Deployment-ready architecture, with AWS only where its value and operating cost are clear.

## Product principles

1. Every factual claim must trace to an eligible source or be marked as interpretation.
2. Publication time, observation time, retrieval time, and historical availability are different fields.
3. Deterministic financial calculations take precedence over free-form model arithmetic.
4. A valid citation does not prove semantic support; evaluation keeps those questions separate.
5. Synthetic data demonstrates mechanics and is never presented as market evidence.
6. Results require baselines, frozen evaluation sets, uncertainty, and limitations.
7. Planned capabilities never appear in the implemented feature list.
8. The product remains an independently developed analytical application, not an investment-advice or production-banking system.

## Documentation standard

The repository must teach a new reader the business problem, architecture, methods, equations, data rights, installation, use, actual results, testing, deployment, limitations, learning connections, and future work. Screenshots and metrics must be genuine and reproducible.

## Governance

Work proceeds in small, reviewed milestones on development branches. `DEVELOPMENT_STATUS.md` records only work actually performed. Merging, deployment, major deletion/replacement, paid services, and creation of new repositories require explicit approval.
