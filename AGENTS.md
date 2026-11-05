# AGENTS.md - vpn-guard

macOS watchdog: freezes AI agent CLIs (SIGSTOP) while the VPN is not `Connected`, resumes them (SIGCONT) when it is back; `run` mode gates the start. Public repo: code, docs and commits in English.

## Tree

- `vpn-guard` - the whole tool, zsh: watch loop and `run` mode
- `local.vpn-guard.plist.in` - LaunchAgent template, `make install` fills `@BIN@` and `@HOME@`
- `test.sh` - checks on a fake process (signed copy of `sleep`), never signals real agents
- `Makefile` - install, uninstall, restart, log, test, lint

## Work

- Mode: PoC. One file, main path only; grow after a real problem shows up.
- Check: `make lint test`. After a change to `vpn-guard`: `make restart`, then `make log`.
- Do not signal real agent processes in tests: the session running the test is one of them.
- Never print `scutil --nc status` in full or run the script with `zsh -x`: the extended status holds the VPN client config with server keys. Only its first line is used.
- `~/bin/vpn-guard` is a symlink to this repo: an edit here is live after `make restart`.
