from pathlib import Path


def current():
    return (Path(__file__).resolve().parent.parent / 'VERSION').read_text('utf-8').strip()
