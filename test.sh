#!/bin/sh
# Checks run mode and freeze/resume on a fake agent process; touches no real agent.
# The resume checks need the configured VPN service to be connected, otherwise they are skipped.
set -u
cd "$(dirname "$0")" || exit 1
tmp=$(mktemp -d)
trap 'kill "$agent" 2>/dev/null; wait "$agent" 2>/dev/null; rm -rf "$tmp"' EXIT
fail=0
ok() { if [ "$1" = "$2" ]; then echo "ok   $3"; else echo "FAIL $3: got '$1', want '$2'"; fail=1; fi; }

# A signed copy of sleep under its own name, so pkill -x matches only it.
cp /bin/sleep "$tmp/fakeagent" && codesign -s - -f "$tmp/fakeagent" 2>/dev/null
"$tmp/fakeagent" 60 &
agent=$!
stat() { ps -o stat= -p "$agent" | cut -c1; }

VPN_GUARD_SERVICE=no-such-vpn ./vpn-guard run true 2>/dev/null
ok $? 1 "run refuses when the VPN is down"

VPN_GUARD_SERVICE=no-such-vpn VPN_GUARD_PROCS=fakeagent ./vpn-guard >"$tmp/down.log" &
guard=$!
sleep 1
ok "$(stat)" T "agent frozen when the VPN is down"
kill "$guard"
sleep 0.5
ok "$(pgrep -P "$guard" | wc -l | tr -d ' ')" 0 "watcher gone after the guard exits"

if ./vpn-guard run true 2>/dev/null; then
  ./vpn-guard run sh -c 'exit 7'
  ok $? 7 "run passes the exit code"
  ok "$(./vpn-guard run printf '%s|' 'a b' c)" "a b|c|" "run passes arguments as is"
  VPN_GUARD_PROCS=fakeagent ./vpn-guard >"$tmp/up.log" &
  guard=$!
  sleep 1
  ok "$(stat)" S "agent resumed when the VPN is up"
  kill "$guard"
else
  echo "skip resume checks: the VPN is not connected"
fi
exit $fail
