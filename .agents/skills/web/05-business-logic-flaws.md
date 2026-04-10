## Business Logic Flaws

- `->` **[Primary Probe]** Map the full application workflow for multi-step processes (checkout, password reset, account upgrade); manually attempt to skip, reorder, or replay individual steps [ieeexplore.ieee](https://ieeexplore.ieee.org/document/11405427/)
  - `->` **[Condition: Skip-step accepted]** → Escalate: access step N+2 without completing N+1 (e.g., confirm order without payment)
  - `->` **[Condition: Price manipulation]** → Intercept quantity/price fields:
    - Negative quantity: `{"qty": -1}` → negative charge / credit addition
    - Float truncation: `{"price": 0.001}` → rounds to 0 at payment
    - Currency mismatch: submit price in low-value currency when backend assumes USD
  - `->` **[Dead End: Server recalculates price server-side]** → Race condition: send concurrent requests to apply the same discount code simultaneously via Turbo Intruder `parallelism=50`
    ```
    engine.queue(target.req, gate='race'); [x50]; engine.openGate('race')
    ```
  - `->` **[Dead End: Race window too small]** → Apply Nagle's algorithm bypass: use HTTP/2 single-packet attack (all requests in one TCP segment)
  - `->` **[Data Chaining]** Duplicate coupon application → free credits → use credits to trigger premium SSRF-capable functionality

***
