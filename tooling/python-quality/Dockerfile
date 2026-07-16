FROM python@sha256:399babc8b49529dabfd9c922f2b5eea81d611e4512e3ed250d75bd2e7683f4b0

LABEL org.opencontainers.image.title="ASEF Python quality toolchain"
LABEL org.opencontainers.image.source="https://github.com/lucasteixeirati/asef-agentic-test-factory"

COPY requirements.lock /tmp/asef-quality-requirements.lock
RUN python -m pip install --no-cache-dir --no-deps --require-hashes -r /tmp/asef-quality-requirements.lock \
    && rm /tmp/asef-quality-requirements.lock

COPY asef_quality_driver.py /opt/asef/asef_quality_driver.py
RUN python -B /opt/asef/asef_quality_driver.py version

WORKDIR /workspace
ENTRYPOINT ["python", "-B", "/opt/asef/asef_quality_driver.py"]
