#!/usr/bin/env python3
"""Exercise run mode inside an interactive shell without a VPN or real agents."""

import os
import pty
import select
import shlex
import signal
import sys
import time
from pathlib import Path


def read_until(fd: int, marker: bytes, timeout: float = 3) -> bytes:
    data = b""
    deadline = time.monotonic() + timeout
    while marker not in data and time.monotonic() < deadline:
        if select.select([fd], [], [], max(0, deadline - time.monotonic()))[0]:
            data += os.read(fd, 65536)
    return data


shell, terminal = pty.fork()
if shell == 0:
    os.execl("/bin/zsh", "zsh", "-f", "-i")
agent = None
try:
    read_until(terminal, b"\x1b[?2004h")
    os.write(terminal, b"PROMPT='VG_PROMPT:%?> '\n")
    read_until(terminal, b"\x1b[?2004h")
    fake = (
        "import os,sys,tty; assert sys.argv[1:]==['a b','c']; tty.setcbreak(0); "
        "os.write(1,b'\\x1b[?1003h\\x1b[?1006h\\x1eREADY:'+str(os.getpid()).encode()+b'\\x1f'); "
        "data=os.read(0,1); os.write(1,b'READ:'+data+b'!\\x1b[?1003l\\x1b[?1006l'); sys.exit(7)"
    )
    command = (
        "function /usr/sbin/scutil { print Connected; }; source "
        + shlex.quote(str(Path(__file__).with_name("vpn-guard")))
        + " run " + shlex.quote(sys.executable) + " -c " + shlex.quote(fake)
        + " 'a b' c"
    )
    # Run in a child zsh, so sourcing the script cannot exit the interactive shell.
    command = ("zsh -fc " + shlex.quote(command) + "\n").encode()
    for mode in ("resume", "interrupt", "paused_interrupt"):
        os.write(terminal, command)
        output = read_until(terminal, b"\x1f")
        assert b"\x1eREADY:" in output, repr(output)
        agent = int(output.rsplit(b"\x1eREADY:", 1)[-1].split(b"\x1f", 1)[0])
        if mode != "resume":
            if mode == "paused_interrupt":
                os.kill(agent, signal.SIGSTOP)
            os.write(terminal, b"\x03")
            if mode == "paused_interrupt":
                output = read_until(terminal, b"VG_PROMPT:", 0.3)
                assert b"VG_PROMPT:" not in output, "Ctrl-C returned prompt while agent was stopped"
                os.kill(agent, signal.SIGCONT)
            output = read_until(terminal, b"VG_PROMPT:130> ")
            assert b"VG_PROMPT:130> " in output, repr(output)
            print(f"ok   {mode} returns status 130")
        else:
            foreground = os.tcgetpgrp(terminal)
            os.kill(agent, signal.SIGSTOP)
            output = read_until(terminal, b"VG_PROMPT:", 0.3)
            assert b"VG_PROMPT:" not in output, "STOP returned the shell prompt"
            assert os.tcgetpgrp(terminal) == foreground, "STOP lost the foreground"
            os.kill(agent, signal.SIGCONT)
            os.write(terminal, b"x")
            output = read_until(terminal, b"VG_PROMPT:7> ")
            assert b"READ:x!" in output and b"VG_PROMPT:7> " in output, repr(output)
            print("ok   STOP/CONT keeps terminal input, arguments and exit status")
        agent = None
finally:
    if agent is not None:
        try:
            os.kill(agent, signal.SIGKILL)
        except ProcessLookupError:
            pass
    os.kill(shell, signal.SIGKILL)
    os.waitpid(shell, 0)
    os.close(terminal)
