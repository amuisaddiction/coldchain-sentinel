# Synthetic demo fixtures

All data in this folder is fictional and intended only for local testing/demo.

Example profile for these fixtures only: 2°C to 8°C, 15-minute expected interval, logger IDs and shipment IDs as shown in each CSV. These values are demo configuration, **not a universal recommendation for medicines**.

- `clean-shipment.csv`: expected to pass configured range checks.
- `excursion-shipment.csv`: expected to flag readings above the configured maximum.
- `evidence-anomaly.csv`: expected to flag logger mismatch (when configured expected logger differs), duplicate timestamp, and out-of-order timestamp.

The custody-gap scenario should be seeded as structured demo events in the application rather than inferred from this CSV.
