## Business Logic Flaws

- **[Primary Probe]** Map multi-step workflows (checkout, password reset, upgrade); attempt to skip, reorder, or replay steps
  - **[Condition: One-shot endpoints]** Identify leak-once secrets and plan state resets before exploit chains
  - **[Condition: Step skip accepted]** Access step N+2 without completing N+1 (confirm order without payment)
  - **[Condition: Price manipulation]** Intercept quantity/price fields:
    - Negative quantity: `{"qty": -1}` → negative charge / credit
    - Float truncation: `{"price": 0.001}` → rounds to 0
    - Currency mismatch: low-value currency when backend assumes USD
  - **[Dead End: Server recalculates]** Race condition: concurrent requests to apply same discount via Turbo Intruder `parallelism=50`
  - **[Dead End: Race window small]** HTTP/2 single-packet attack (all requests in one TCP segment)
  - **[Condition: PRNG sequencing]** Capture outputs to recover state and predict protocol artifacts (IDs, boundaries, nonces)
  - **[Data Chaining]** Duplicate coupon → free credits → premium SSRF functionality

***
