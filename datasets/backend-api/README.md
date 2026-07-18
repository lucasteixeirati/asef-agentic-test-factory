# Backend API conformance dataset

This bounded dataset maps the minimum Stage 6.3 controls to executable regression
oracles in `tests/test_backend_api_conformance.py`. It contains no credentials,
external targets or mutable operations. `ACCEPTED` means only that the declared
contract was accepted; `POLICY_BLOCKED` means rejection occurred before network
execution.

The dataset does not authorize public-network traffic. Runtime execution remains
restricted to literal loopback addresses and explicitly allowed ports.
