FROM mcr.microsoft.com/playwright@sha256:57b65fdc9ceabe0ef613124c7bbe2babcf9362c4d85e382fe3b03604e84b428a AS dependencies

ARG SOURCE_DATE_EPOCH=0

ENV PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1

WORKDIR /opt/asef-web-ui
COPY package.json package-lock.json ./
COPY asef_web_ui_driver.mjs ./asef_web_ui_driver.mjs
RUN npm ci --omit=dev --ignore-scripts --no-audit --no-fund \
    && chmod 0555 asef_web_ui_driver.mjs \
    && tar --sort=name --format=posix \
        --pax-option=exthdr.name=%d/PaxHeaders/%f,delete=atime,delete=ctime \
        --mtime="@${SOURCE_DATE_EPOCH}" --clamp-mtime \
        --owner=0 --group=0 --numeric-owner \
        -cf /tmp/asef-web-ui-toolchain.tar . \
    && touch -h -d "@${SOURCE_DATE_EPOCH}" /tmp/asef-web-ui-toolchain.tar \
    && sha256sum /tmp/asef-web-ui-toolchain.tar

FROM mcr.microsoft.com/playwright@sha256:57b65fdc9ceabe0ef613124c7bbe2babcf9362c4d85e382fe3b03604e84b428a

ARG SOURCE_DATE_EPOCH=0

LABEL org.opencontainers.image.title="ASEF Web UI Playwright toolchain"
LABEL org.opencontainers.image.source="https://github.com/lucasteixeirati/asef-agentic-test-factory"
LABEL com.asef.playwright.version="1.61.0"
LABEL com.asef.chromium.version="149.0.7827.55"

ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 \
    HOME=/tmp/asef-home

WORKDIR /opt/asef-web-ui
COPY --from=dependencies /tmp/asef-web-ui-toolchain.tar /tmp/asef-web-ui-toolchain.tar
RUN tar -xf /tmp/asef-web-ui-toolchain.tar -C /opt/asef-web-ui \
    && rm /tmp/asef-web-ui-toolchain.tar \
    && find /opt/asef-web-ui -exec touch -h -d "@${SOURCE_DATE_EPOCH}" {} + \
    && node /opt/asef-web-ui/asef_web_ui_driver.mjs version

WORKDIR /workspace
ENTRYPOINT ["node", "/opt/asef-web-ui/asef_web_ui_driver.mjs"]
