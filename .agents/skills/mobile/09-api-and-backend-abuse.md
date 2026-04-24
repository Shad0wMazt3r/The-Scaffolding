## API & Backend Abuse from Mobile Context

- * -> [Condition: Endpoint inventory exists] -> Action: Primary Probe: build a mobile-specific API map from intercepted traffic, hardcoded URLs, GraphQL docs, protobuf schemas, and hidden feature flags.
  - * -> [Condition: Straight request tampering shows no issue] -> Action: Dead End Pivot 1: test mobile-only headers, version gates, locale/device claims, and hidden parameters lifted from static analysis.
  - * -> [Condition: Authz looks consistent on obvious routes] -> Action: Dead End Pivot 2: pivot to secondary object types such as invoices, tickets, media, drafts, or notification settings where mobile backends often lag web controls.
  - * -> [Condition: REST looks hardened] -> Action: Dead End Pivot 3: probe batch APIs, GraphQL introspection remnants, websocket channels, file uploads, and pre-signed URL issuance flows.
  - * -> [Condition: Secret or mobile key was found statically] -> Action: Data Chaining: use that key to emulate the app, authenticate hidden endpoints, enumerate objects, then combine any IDOR with session/token weakness for takeover or horizontal/vertical access.
  - * -> [Condition: Server trusts client-calculated values] -> Action: test discounts, reward balances, KYC states, or entitlement flags modified from rooted runtime hooks.
- * -> [Condition: Mobile transport is different from browser transport] -> Action: keep separate replay collections for app-only headers, protobuf bodies, certificate-bound flows, and feature-flag endpoints.

