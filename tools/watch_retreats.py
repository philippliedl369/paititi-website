#!/usr/bin/env python3
"""Ask Retreat Guru whether the site is behind, and say so on the desktop.

Retreat Guru is the one source this repo depends on that nobody here
controls. Roman edits a program over there and nothing on this machine
knows: the pages keep matching data/retreats.json, `npm run check` keeps
passing, and the site shows the old words until somebody happens to look.
That is how the New York talk had no page on this site for two days.

So this asks once a morning and only speaks when the answer is "yes, you're
behind" — the same shape as the trading hub's alerts: a notification, and a
line appended to a log you can read later.

    python3 tools/watch_retreats.py            # ask now; silent if in step
    python3 tools/watch_retreats.py --test     # force the notification path

Why Python and not the obvious shell script: under launchd, `/bin/bash`
cannot read anything under ~/Desktop — macOS TCC denies it and the job dies
with "Operation not permitted" before the script's first line. The
python3 in /Library/Frameworks has been granted Full Disk Access (it is what
the trading hub runs), so naming *that* interpreter in the plist is what
makes this work at all. Don't convert it back to a .sh.
"""
import os
import pathlib
import subprocess
import sys
from datetime import datetime

REPO = pathlib.Path(__file__).resolve().parent.parent
LOG = REPO / 'tools' / '.retreat-watch.log'
BRANCH = 'replica-fidelity-chrome-home'
GIT = '/usr/bin/git'


def now():
    return datetime.now().astimezone().strftime('%Y-%m-%dT%H:%M:%S%z')


APP = pathlib.Path.home() / 'Applications' / 'Paititi Watch.app'
MSG_FILE = pathlib.Path('/tmp/paititi-watch-message.txt')


def notify(message, title='paititi site'):
    """A banner, and nothing that can fail loudly.

    Posted through Paititi Watch.app when it is built, because a notification
    always shows the *posting* app's icon — straight osascript means Script
    Editor's scroll, which is indistinguishable at a glance from the trading
    hub's alerts. Falls back to osascript if the app isn't there, so a fresh
    checkout still alerts; `bash tools/notifier/build.sh` creates it.

    The message goes via /tmp rather than an argument: `open -a` will not
    relaunch a running app and would drop it silently."""
    safe = message.replace('\\', '').replace('"', "'")[:230]
    try:
        if APP.exists():
            MSG_FILE.write_text(safe, encoding='utf-8')
            subprocess.run(['/usr/bin/open', '-a', str(APP)],
                           timeout=15, check=False, capture_output=True)
            return
        subprocess.run(['/usr/bin/osascript', '-e',
                        'display notification "%s" with title "%s"' % (safe, title)],
                       timeout=10, check=False, capture_output=True)
    except Exception:
        pass


def behind_origin():
    """How many commits origin has that we don't — reported, never merged.
    A background job that moved the working tree under you would be worse
    than the problem it solves. Any failure here is silent: it is a footnote
    to the alert, not the point of it."""
    try:
        subprocess.run([GIT, 'fetch', '--quiet', 'origin', BRANCH],
                       cwd=REPO, timeout=60, check=False, capture_output=True)
        out = subprocess.run([GIT, 'rev-list', '--count', 'HEAD..origin/%s' % BRANCH],
                             cwd=REPO, timeout=30, check=False, capture_output=True)
        return int(out.stdout.decode().strip() or 0)
    except Exception:
        return 0


def main():
    if '--test' in sys.argv:
        notify('Test — this is what a Retreat Guru change looks like.')
        print('%s test notification sent' % now())
        return 0

    proc = subprocess.run([sys.executable, str(REPO / 'tools' / 'gen_retreats.py'),
                           '--check-live'],
                          cwd=REPO, capture_output=True, timeout=300)
    out = (proc.stdout + proc.stderr).decode('utf-8', 'replace').rstrip()

    # The log records every run, in step or not. A watcher that quietly died
    # looks exactly like good news, and this is the only thing that tells
    # the two apart.
    with LOG.open('a', encoding='utf-8') as f:
        f.write('%s exit=%d\n' % (now(), proc.returncode))
        for line in out.splitlines():
            f.write('    %s\n' % line)

    print(out)
    if proc.returncode == 0:
        return 0

    programs = [l for l in out.splitlines() if l.strip().startswith('- ')]
    msg = 'Retreat Guru changed %d program(s). Run: npm run gen-retreats' % len(programs)
    n = behind_origin()
    if n:
        msg += ' (git pull first — %d behind)' % n
    notify(msg)
    return 1


if __name__ == '__main__':
    sys.exit(main())
