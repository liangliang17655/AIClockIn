"""Uninstall only the current user's task that targets this exact installed program/data."""
from pathlib import Path
import xml.etree.ElementTree as ET
from .schedule import WindowsTask, NS, arguments


def remove_own_task(exe,data,backend=None):
    backend=backend or WindowsTask()
    xml=backend.get()
    if not xml:return 0
    root=ET.fromstring(xml)
    target=root.findtext('t:Actions/t:Exec/t:Command',namespaces=NS)
    args=root.findtext('t:Actions/t:Exec/t:Arguments',namespaces=NS)
    user=root.findtext('t:Principals/t:Principal/t:UserId',namespaces=NS)
    if not target or Path(target).resolve()!=Path(exe).resolve():return 0
    if args!=arguments(data) or user!=backend.user:
        raise RuntimeError('自动任务身份或数据路径不匹配，未删除任务')
    backend.remove()
    if backend.get() is not None:raise RuntimeError('自动任务未能移除')
    return 0
