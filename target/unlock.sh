#!/bin/sh
# unlock <host> <credential>
#
# Static gate logic. Per-run data (one row per host: name, credential hash,
# base64 payload) lives in /target/.gatedata, written by build_target.py.
# Verifies the credential by hash — so reading this script or the data reveals
# only hashes, never a credential. On success, materialises the host and logs
# the event; a wrong credential is logged as a denial.
host="$1"; cred="$2"
data=/target/.gatedata
log=/target/unlock.log

if [ -z "$host" ] || [ -z "$cred" ]; then
  echo "usage: unlock <host> <credential>"; exit 2
fi

row=$(awk -F'\t' -v k="$host" '$1==k {print; exit}' "$data")
if [ -z "$row" ]; then
  echo "unknown host: $host"; exit 1
fi

want=$(printf '%s' "$row" | cut -f2)
blob=$(printf '%s' "$row" | cut -f3)
got=$(printf '%s' "$cred" | sha256sum | cut -d' ' -f1)

if [ "$got" != "$want" ]; then
  echo "$(date -u +%FT%TZ) DENY $host" >> "$log"
  echo "access denied for $host"; exit 1
fi

mkdir -p "/target/$host"
printf '%s' "$blob" | base64 -d > "/target/$host/notes"
echo "$(date -u +%FT%TZ) UNLOCK $host" >> "$log"
echo "unlocked $host -> /target/$host/notes"
