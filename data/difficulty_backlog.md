# Difficulty Backlog

The current dataset in `tickets_phaseA.jsonl` includes only `easy` and `medium` tickets.
Difficulty for each ticket can be cross referenced via `ticket_id` in `data/expected_results_phaseA.jsonl`.

Planned additions for Phase A hard-mode coverage:
- [ ] Authentication outage scenario with multi-tenant impact (label: `hard`).
- [ ] Billing reconciliation edge case requiring cross-team coordination (label: `hard`).
- [ ] Incident involving third-party dependency degradation (label: `hard`).
- [ ] Security escalation with immediate containment requirements (label: `hard`).

Add these once smoke tests and CI gates are stable to stress accuracy and cost controls.
