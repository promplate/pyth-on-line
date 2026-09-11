FROM vllm/vllm-openai-cpu:v0.28.0-x86_64

USER root
WORKDIR /opt/vllm-hmr

# Install the HMR package from this checkout, not from an unpinned wheel.
COPY packages/hmr /opt/hmr-source
RUN /opt/venv/bin/pip install --no-deps /opt/hmr-source

# Copy the example so the container is self-contained.
COPY examples/vllm-cpu-hmr /opt/vllm-hmr
RUN /opt/venv/bin/pip install --no-deps /opt/vllm-hmr

# pyth-on-line excludes virtualenv/site-packages paths. Keep the official
# release bytes, but expose them from an external source root for this probe.
RUN mkdir -p /opt/vllm-release-source \
    && cp -a /opt/venv/lib/python3.12/site-packages/vllm /opt/vllm-release-source/

ENV PYTHONPATH=/opt/vllm-hmr:/opt/vllm-release-source
ENTRYPOINT ["python3", "/opt/vllm-hmr/smoke.py"]
