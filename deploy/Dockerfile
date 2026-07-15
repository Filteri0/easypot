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
# etc.). Defaults here keep a bare `docker run` working.
ENV HONEYPOT_PORT=2222 \
    HONEYPOT_HOSTNAME=svr04 \
    EASYPOT_AUDIT_JSONL=/data/audit/events.jsonl \
    HONEYPOT_HOST_KEY=/data/keys/ssh_host_rsa_key

EXPOSE 2222

# Shell form so the env vars expand. --host-key persists the key across restarts
# (stable fingerprint); --audit-jsonl is also read from EASYPOT_AUDIT_JSONL, set
# here explicitly for clarity.
CMD python -m honeyshell \
      --host 0.0.0.0 \
      --port "$HONEYPOT_PORT" \
      --hostname "$HONEYPOT_HOSTNAME" \
      --host-key "$HONEYPOT_HOST_KEY" \
      --audit-jsonl "$EASYPOT_AUDIT_JSONL"
