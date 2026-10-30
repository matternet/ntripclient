#!/bin/bash
# Usage: test/run_client.sh <port> <duration_sec> <outprefix>
# Runs ../ntripclient against a mock caster on 127.0.0.1:<port>, feeding a fresh
# GGA to its stdin every 1 s the way MATE does. Captures stdout (RTCM) to
# <outprefix>.rtcm and stderr (log) to <outprefix>.err; prints exit code and
# RTCM byte count. See test/README.md for the scenarios.
PORT=$1; DUR=$2; OUT=$3
BIN="$(cd "$(dirname "$0")/.." && pwd)/ntripclient"
GGA='$GPGGA,055234.000,3714.7258,N,12224.3666,W,4,10,1.2,67,M,,M,,*5C'
(
  i=0
  while [ $i -lt $DUR ]; do
    printf '$GPGGA,%06d.000,3714.7258,N,12224.3666,W,4,10,1.2,67,M,,M,,*5C\r\n' $i
    sleep 1
    i=$((i+1))
  done
) | "$BIN" -s 127.0.0.1 -r "$PORT" -m MOCK -u u -p p -M h -n "$GGA" > "$OUT.rtcm" 2> "$OUT.err" &
CPID=$!
for ((t=0; t<DUR; t++)); do
  kill -0 $CPID 2>/dev/null || break
  sleep 1
done
if kill -0 $CPID 2>/dev/null; then
  kill $CPID 2>/dev/null; wait $CPID 2>/dev/null; echo "EXIT=killed-after-${DUR}s"
else
  wait $CPID; echo "EXIT=$?"
fi
echo "RTCM_BYTES=$(wc -c < "$OUT.rtcm" | tr -d ' ')"
