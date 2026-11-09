# Hackathon Demo Script (target: 2–3 minutes)

## Opening (15 sec)
"Cold-chain monitoring tells us what happened to a shipment. ColdChain Sentinel connects that evidence to a transparent acceptance decision and payment workflow."

## Scenario 1: Clean shipment (35 sec)
- Open seeded clean shipment.
- Show product-specific configured range and source.
- Upload/inspect logger CSV.
- Show complete evidence checks, temperature graph, custody timeline.
- Reviewer approves with a reason.
- Show actual PayPal sandbox capture result, or visibly labelled Demo Mode simulation.

## Scenario 2: Temperature excursion (35 sec)
- Open excursion shipment.
- Show exact out-of-range readings and time window.
- Explain that this is a configured-limit breach, not a claim that medicine is clinically unsafe.
- Reviewer rejects.
- Show PayPal sandbox authorisation voided, or Demo Mode simulation.

## Scenario 3: Evidence anomaly (35 sec)
- Open malformed/mismatched evidence case.
- Show missing timestamps, duplicate/out-of-order rows, or logger mismatch.
- Explain why the system refuses to capture.
- Route to manual review/request evidence.

## Scenario 4: Custody gap (20 sec)
- Show missing handover event and resulting review requirement.

## Close (15 sec)
"Every decision is traceable to evidence, a configured rule, a human reviewer, and the actual payment state."

## Demo discipline
- Do not claim real medicines were monitored.
- Do not claim regulatory certification.
- Do not claim a simulated payment is a PayPal transaction.
- Do not say an upload is tamper-proof; explain exactly what hash and metadata checks can and cannot establish.
