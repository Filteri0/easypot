# Log collector image — pure stdlib, no dependencies.
#
# IMPORTANT: uses the SAME uid/gid (10001) as the honeypot image. Both mount the
# shared "audit" volume, and Docker seeds a fresh named volume's owner/mode from
# whichever image's directory it first initialises from. If the two images used
# different uids, the volume would be owned by one and unwritable by the other
# (the crash-loop we hit). One uid everywhere = no permission fight.
FROM python:3.12-slim

# 10001 = the easypot uid (see deploy/Dockerfile). Group name "app" is arbitrary;
# the number is what matters for the shared volume.
RUN groupadd --gid 10001 app && \
    useradd --create-home --uid 10001 --gid 10001 app
WORKDIR /app
COPY deploy/collector/collect.py ./collect.py
RUN mkdir -p /data/audit && chown -R 10001:10001 /data /app
USER 10001:10001

ENV AUDIT_DIR=/data/audit \
    MERGED_OUT=/data/audit/_merged.jsonl \
    POLL_INTERVAL=1.0

CMD ["python", "collect.py"]
