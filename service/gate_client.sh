#!/bin/sh
# gate <host> <credential> — submit one attempt to the gatekeeper and wait.
# Prints BUSY (rate-limited, retry), DENY (wrong), or "OK" + the revealed payload.
[ -z "$1" ] || [ -z "$2" ] && { echo "usage: gate <host> <credential>"; exit 2; }
id="$$_$(awk 'BEGIN{srand();print int(rand()*99999)}')"
echo "$1 $2" > "/drop/req_$id"
i=0
while [ $i -lt 60 ]; do
  if [ -f "/drop/resp_$id" ]; then cat "/drop/resp_$id"; rm -f "/drop/resp_$id"; exit 0; fi
  sleep 0.1; i=$((i+1))
done
echo "TIMEOUT"
