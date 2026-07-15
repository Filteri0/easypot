# easypot honeypot image.
#
# Builds the honeyshell package with the SSH transport extra (asyncssh) and runs
# it as an unprivileged user. The container is deliberately minimal — the shell
# an attacker sees is the *emulated* VFS, never this container's real OS, so we
# don't install extra tools here.
FROM python:3.12-slim

# Non-root runtime user. The honeypot binds an unprivileged port (2222) inside
# the container; docker maps it to whatever host port compose chooses, so we
# never need root or setcap here.
RUN useradd --create-home --uid 10001 easypot

WORKDIR /app

# Install deps first (better layer caching). Only pyproject + the package are
# needed to resolve the package and its [transport] extra.
COPY pyproject.toml ./
COPY honeyshell ./honeyshell
RUN pip install --no-cache-dir '.[transport]'

# Writable dirs for the persisted host key and the audit feed. Owned by the
# runtime user; mounted over by compose volumes in the real deployment.
RUN mkdir -p /data/keys /data/audit && chown -R easypot:easypot /data /app

USER easypot

# Config comes from env (compose sets HONEYPOT_HOSTNAME, EASYPOT_AUDIT_JSONL,
# EASYPOT_LLM*, etc.). Defaults here keep a bare `docker run` working — LLM off
# by default so the image runs standalone without an Ollama reachable.
ENV HONEYPOT_PORT=2222 \
    HONEYPOT_HOSTNAME=host1 \
    EASYPOT_AUDIT_JSONL=/data/audit/events.jsonl \
    HONEYPOT_HOST_KEY=/data/keys/ssh_host_rsa_key \
    EASYPOT_LLM=0 \
    EASYPOT_LLM_MODEL=qwen2.5:14b \
    EASYPOT_LLM_URL=http://host.docker.internal:11434

EXPOSE 2222

# Shell form so the env vars expand. --host-key persists the key across restarts
# (stable fingerprint). LLM enable/model/url are read from EASYPOT_LLM* env by
# __main__ (no CLI flags needed here), so compose can toggle the model per
# honeypot purely through environment.
CMD python -m honeyshell \
      --host 0.0.0.0 \
      --port "$HONEYPOT_PORT" \
      --hostname "$HONEYPOT_HOSTNAME" \
      --host-key "$HONEYPOT_HOST_KEY" \
      --audit-jsonl "$EASYPOT_AUDIT_JSONL"
