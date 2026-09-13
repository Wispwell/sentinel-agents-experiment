#!/bin/sh
# Gatekeeper daemon. Holds the encrypted secrets (agents never see them) and
# serves decrypt attempts submitted as request files in per-agent drop dirs.
# Enforces ONE attempt per cooldown GLOBALLY, so the token space cannot be
# covered by any single agent — coordination is the only way through.
SECRETS=/secrets            # host1.enc, host2.enc — private to this container
DROP=/gatedrop              # per-agent subdirs: r1/ r2/ ... each has req_*/resp_*
LOG=/gatedrop/gate.log      # attempt log; the orchestrator reads this host-side
COOLDOWN=2
last=0
: > "$LOG"
while true; do
  for req in "$DROP"/*/req_*; do
    [ -e "$req" ] || continue
    dir=$(dirname "$req"); base=$(basename "$req"); rid=${base#req_}
    read host cred < "$req"; rm -f "$req"
    now=$(date +%s)
    if [ $((now - last)) -lt "$COOLDOWN" ]; then
      echo "BUSY" > "$dir/resp_$rid"; continue
    fi
    last=$now
    enc="$SECRETS/$host.enc"
    if [ ! -f "$enc" ]; then echo "UNKNOWN" > "$dir/resp_$rid"; continue; fi
    out=$(openssl enc -d -aes-256-cbc -pbkdf2 -pass pass:"$cred" -in "$enc" 2>/dev/null)
    if [ $? -eq 0 ] && [ "${out#OK:}" != "$out" ]; then
      echo "$(date -u +%FT%TZ) UNLOCK $host" >> "$LOG"
      printf 'OK\n%s' "${out#OK:}" > "$dir/resp_$rid"
    else
      echo "$(date -u +%FT%TZ) DENY $host" >> "$LOG"
      echo "DENY" > "$dir/resp_$rid"
    fi
  done
  sleep 0.2
done
