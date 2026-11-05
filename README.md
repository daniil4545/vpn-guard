# vpn-guard

A macOS watchdog that freezes AI agent CLIs while your VPN is off, so the AI provider never sees your real IP.

You turn the VPN off for a minute and type into an open agent session by accident; or the agent keeps working on its own. vpn-guard sends `SIGSTOP` to the agent processes the moment the VPN status leaves `Connected` and `SIGCONT` when it is back. Text typed meanwhile waits in the terminal and goes out through the VPN.

It also gates the start: `vpn-guard run claude` starts the command only while the VPN is connected.

## How it works

- Watches network and VPN state keys in configd (`scutil n.watch`) and rechecks every 5 seconds as a fallback.
- The VPN state is `scutil --nc status "<service>"`. Anything but `Connected` counts as down, including `Disconnecting`, so agents freeze before the tunnel is torn down.
- Freezes by exact process name (`pkill -x`). Agents started while the VPN is down are frozen on the next check.
- Logs every state change to `~/Library/Logs/vpn-guard.log`, with the default route interface at freeze time (`route=utun1` means the tunnel was still up).

Idle cost is about 0.02 s of CPU per 30 s plus one `scutil` call every 5 s.

## Limits

- A request sent in the gap between the VPN going down and the next check leaves with your real IP. For a manual disconnect the gap is a configd event; for a crashed VPN client it can be up to the poll interval.
- A frozen agent ignores Ctrl+C until the VPN is back.
- This is not a kill switch: other apps keep using the network. For a hard block use `pf` or your VPN client's kill switch.

## Install

```sh
make install    # symlink to ~/bin/vpn-guard, LaunchAgent local.vpn-guard, started at login
make log        # last 20 log lines
make uninstall
```

Gate the start in `~/.zshrc`:

```sh
claude() { ~/bin/vpn-guard run claude "$@"; }
codex()  { ~/bin/vpn-guard run codex "$@"; }
```

## Settings

Environment variables, set in the LaunchAgent plist for the watchdog:

| Variable | Default | Meaning |
| --- | --- | --- |
| `VPN_GUARD_SERVICE` | `Sota Connect` | VPN service name from `scutil --nc list` |
| `VPN_GUARD_PROCS` | `claude codex` | process names to freeze |
| `VPN_GUARD_POLL` | `5` | fallback check interval, seconds |

## Test

```sh
make test   # run mode and freeze/resume on a fake process; resume checks need the VPN connected
```

## License

MIT
