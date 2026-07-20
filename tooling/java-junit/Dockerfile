FROM maven@sha256:2b4496088e7b80ae10a8c9f74e574ea21380325a006ec684532ad6bad5bc7273 AS dependencies

WORKDIR /opt/bootstrap
COPY bootstrap/ ./
RUN mvn --batch-mode --no-transfer-progress -Dmaven.repo.local=/opt/asef-m2 test \
    && rm -rf /opt/bootstrap /opt/asef-m2/com/asef \
    && chmod -R a-w /opt/asef-m2

FROM maven@sha256:2b4496088e7b80ae10a8c9f74e574ea21380325a006ec684532ad6bad5bc7273

LABEL org.opencontainers.image.title="ASEF Java JUnit toolchain"
LABEL org.opencontainers.image.source="https://github.com/lucasteixeirati/asef-agentic-test-factory"
LABEL com.asef.java.version="21.0.11"
LABEL com.asef.maven.version="3.9.16"
LABEL com.asef.junit.version="5.13.4"
LABEL com.asef.surefire.version="3.5.5"

ENV HOME=/tmp/asef-home
COPY --from=dependencies /opt/asef-m2 /opt/asef-m2
COPY asef_java_driver.sh /opt/asef-java/asef_java_driver.sh
RUN chmod 0555 /opt/asef-java/asef_java_driver.sh \
    && /opt/asef-java/asef_java_driver.sh version

WORKDIR /workspace
ENTRYPOINT ["/opt/asef-java/asef_java_driver.sh"]
