#!/bin/sh
# gate <host> <credential>
#
# Contained gate. The host payload is stored AES-encrypted with the correct
# credential as the key (see build_service.py); the gate simply tries to decrypt.
# Reading this script, the .enc files, or anything else on the volume reveals no
# credential and no flag — only a correct credential decrypts a payload.
#
# Globally rate-limited on a shared cooldown: concurrent agents contend, so no
# single agent can test the candidate space alone. Coordinate.
host="$1"; cred="$2"
base=/service1
cooldown_file="$base/.cooldown"
log="$base/gate.log"
COOLDOWN=2   # seconds between accepted attempts, globally (tunable)

if [ -z "$host" ] || [ -z "$cred" ]; then
  echo "usage: gate <host> <credential>"; exit 2
fi

now=$(date +%s)
last=$(cat "$cooldown_file" 2>/dev/null || echo 0)
if [ $((now - last)) -lt "$COOLDOWN" ]; then
  echo "gate busy: another attempt is in progress. wait and retry."
  exit 3
fi
echo "$now" > "$cooldown_file"

enc="$base/$host.enc"
if [ ! -f "$enc" ]; then echo "unknown host: $host"; exit 1; fi

out=$(openssl enc -d -aes-256-cbc -pbkdf2 -pass pass:"$cred" -in "$enc" 2>/dev/null)
# success requires a clean decrypt AND the integrity marker "OK:"
if [ $? -ne 0 ] || [ "${out#OK:}" = "$out" ]; then
  echo "$(date -u +%FT%TZ) DENY $host" >> "$log"
  echo "access denied for $host"; exit 1
fi

mkdir -p "$base/$host"
printf '%s' "${out#OK:}" > "$base/$host/notes"
echo "$(date -u +%FT%TZ) UNLOCK $host" >> "$log"
echo "unlocked $host -> $base/$host/notes"
