# Evidence graph and operations

D7.1 adds a small point-in-time provenance graph connecting one company, filing, passage, fact, event, and fixture instrument. Nodes and edges have evidence URIs and availability times; loads fail on duplicate IDs, dangling references, unsupported relationship types, or causal language.

The graph uses `filed`, `contains`, `supports`, `describes`, and `linked_to`. `linked_to` means an identifier relationship only. It does not mean a filing event caused a market move. Bounded path traversal avoids revisiting cycles and never exceeds the requested hop limit.

The operations report verifies required repository files, records the graph SHA-256, and labels the current acceptance target `verified_local_demo_not_hosted`. It does not claim deployment, backups, service-level objectives, or production readiness.
