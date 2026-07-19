# Web UI conformance dataset

This bounded dataset maps every Stage 6.4.5 control to executable oracles in
`tests/test_web_ui_conformance.py` and
`tests/integration/test_web_ui_conformance_docker.py`. The normal fixture remains
local, resettable and free of egress APIs. `conformance.html` is a separate,
controlled adversarial page used only to prove that external requests, popups,
dialogs and downloads fail closed inside Chromium.

Docker cases run with `--network none`; the external request uses the documentation
address `192.0.2.1` and is intercepted by Playwright before transport. Screenshots
are failure-only private evidence. Functional fingerprints intentionally exclude
duration and private file names and must remain identical over two repetitions.
