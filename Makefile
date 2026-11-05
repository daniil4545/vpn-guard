BIN    ?= $(HOME)/bin
AGENTS := $(HOME)/Library/LaunchAgents
PLIST  := $(AGENTS)/local.vpn-guard.plist
DOMAIN := gui/$(shell id -u)

.PHONY: install uninstall restart log test lint commit-check

install:
	mkdir -p $(BIN) $(AGENTS)
	ln -sf $(CURDIR)/vpn-guard $(BIN)/vpn-guard
	sed -e 's|@BIN@|$(BIN)|' -e 's|@HOME@|$(HOME)|' local.vpn-guard.plist.in > $(PLIST)
	-launchctl bootout $(DOMAIN)/local.vpn-guard 2>/dev/null
	@while launchctl print $(DOMAIN)/local.vpn-guard >/dev/null 2>&1; do sleep 0.2; done
	launchctl bootstrap $(DOMAIN) $(PLIST)
	@launchctl print $(DOMAIN)/local.vpn-guard | grep -m1 'state ='

uninstall:
	-launchctl bootout $(DOMAIN)/local.vpn-guard
	rm -f $(PLIST) $(BIN)/vpn-guard

restart:
	launchctl kickstart -k $(DOMAIN)/local.vpn-guard

log:
	tail -n 20 $(HOME)/Library/Logs/vpn-guard.log

test:
	./test.sh

lint:
	zsh -n vpn-guard
	shellcheck test.sh

commit-check: lint
