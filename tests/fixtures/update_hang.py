"""Only built for the isolated frozen self-test timeout test; never shipped."""
import os
from pathlib import Path
import subprocess
import sys
import time

report = Path(sys.argv[sys.argv.index('--report') + 1])
if '--hang-child' not in sys.argv:
    subprocess.Popen([sys.executable, '--hang-child', '--report', str(report)],
                     env={**os.environ, 'PYINSTALLER_RESET_ENVIRONMENT': '1'},
                     creationflags=subprocess.CREATE_NO_WINDOW)
else:
    report.with_suffix('.child-pid').write_text(str(os.getpid()), encoding='ascii')
time.sleep(300)
