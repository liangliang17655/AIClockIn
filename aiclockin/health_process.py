"""A suspended Windows process assigned to a kill-on-close Job before any code runs."""
import ctypes as c
from ctypes import wintypes as w
import os
import subprocess
import time


class Startup(c.Structure):
    _fields_ = [('cb', w.DWORD), ('reserved', w.LPWSTR), ('desktop', w.LPWSTR), ('title', w.LPWSTR),
                ('x', w.DWORD), ('y', w.DWORD), ('width', w.DWORD), ('height', w.DWORD),
                ('chars_x', w.DWORD), ('chars_y', w.DWORD), ('fill', w.DWORD), ('flags', w.DWORD),
                ('show', w.WORD), ('reserved_size', w.WORD), ('reserved_data', c.c_void_p),
                ('stdin', w.HANDLE), ('stdout', w.HANDLE), ('stderr', w.HANDLE)]


class ProcessInfo(c.Structure):
    _fields_ = [('process', w.HANDLE), ('thread', w.HANDLE), ('pid', w.DWORD), ('tid', w.DWORD)]


class BasicLimits(c.Structure):
    _fields_ = [('process_time', c.c_int64), ('job_time', c.c_int64), ('flags', w.DWORD),
                ('min_ws', c.c_size_t), ('max_ws', c.c_size_t), ('active_limit', w.DWORD),
                ('affinity', c.c_size_t), ('priority', w.DWORD), ('scheduling', w.DWORD)]


class Io(c.Structure):
    _fields_ = [(name, c.c_uint64) for name in ('reads', 'writes', 'other', 'read_bytes', 'write_bytes', 'other_bytes')]


class ExtendedLimits(c.Structure):
    _fields_ = [('basic', BasicLimits), ('io', Io), ('process_memory', c.c_size_t),
                ('job_memory', c.c_size_t), ('peak_process', c.c_size_t), ('peak_job', c.c_size_t)]


class Accounting(c.Structure):
    _fields_ = [('user', c.c_int64), ('kernel', c.c_int64), ('period_user', c.c_int64),
                ('period_kernel', c.c_int64), ('faults', w.DWORD), ('total', w.DWORD),
                ('active', w.DWORD), ('terminated', w.DWORD)]


class HealthProcess:
    def __init__(self, command, cwd, env):
        self.command, self.cwd, self.env = command, cwd, env

    def __enter__(self):
        api = self.api = c.WinDLL('kernel32', use_last_error=True)
        api.CreateJobObjectW.argtypes = [c.c_void_p, w.LPCWSTR]; api.CreateJobObjectW.restype = w.HANDLE
        api.SetInformationJobObject.argtypes = [w.HANDLE, c.c_int, c.c_void_p, w.DWORD]
        api.AssignProcessToJobObject.argtypes = [w.HANDLE, w.HANDLE]
        api.QueryInformationJobObject.argtypes = [w.HANDLE, c.c_int, c.c_void_p, w.DWORD, c.c_void_p]
        api.CreateProcessW.argtypes = [w.LPCWSTR, w.LPWSTR, c.c_void_p, c.c_void_p, w.BOOL, w.DWORD,
                                      c.c_void_p, w.LPCWSTR, c.POINTER(Startup), c.POINTER(ProcessInfo)]
        api.ResumeThread.argtypes = [w.HANDLE]; api.ResumeThread.restype = w.DWORD
        api.TerminateJobObject.argtypes = [w.HANDLE, w.UINT]
        api.TerminateProcess.argtypes = [w.HANDLE, w.UINT]
        api.WaitForSingleObject.argtypes = [w.HANDLE, w.DWORD]; api.WaitForSingleObject.restype = w.DWORD
        api.GetExitCodeProcess.argtypes = [w.HANDLE, c.POINTER(w.DWORD)]
        api.CloseHandle.argtypes = [w.HANDLE]
        self.job = api.CreateJobObjectW(None, None)
        self.info = ProcessInfo()
        try:
            limits = ExtendedLimits(); limits.basic.flags = 0x2000  # KILL_ON_JOB_CLOSE, no breakaway.
            if not self.job or not api.SetInformationJobObject(self.job, 9, c.byref(limits), c.sizeof(limits)):
                raise OSError('无法创建隔离自检作业')
            startup = Startup(); startup.cb = c.sizeof(startup)
            command = c.create_unicode_buffer(subprocess.list2cmdline(self.command))
            block = c.create_unicode_buffer('\0'.join(f'{k}={v}' for k, v in sorted(self.env.items())) + '\0\0')
            if not api.CreateProcessW(self.command[0], command, None, None, False,
                                      0x08000000 | 0x4 | 0x400, block, str(self.cwd), c.byref(startup), c.byref(self.info)):
                raise OSError('无法启动新版离线自检')
            if not api.AssignProcessToJobObject(self.job, self.info.process):
                raise OSError('无法隔离新版自检进程')
            if api.ResumeThread(self.info.thread) == 0xFFFFFFFF:
                raise OSError('无法运行新版自检')
            return self
        except Exception:
            if self.info.process:
                api.TerminateProcess(self.info.process, 1)
                api.WaitForSingleObject(self.info.process, 10000)
            self.close()
            raise

    def wait(self, timeout):
        result = self.api.WaitForSingleObject(self.info.process, int(timeout * 1000))
        if result == 258:
            raise subprocess.TimeoutExpired(self.command, timeout)
        if result != 0:
            raise OSError('等待自检进程失败')
        code = w.DWORD()
        if not self.api.GetExitCodeProcess(self.info.process, c.byref(code)):
            raise OSError('读取自检结果失败')
        return code.value

    def close(self):
        api = self.api
        if self.job:
            api.TerminateJobObject(self.job, 1)
            # Wait for every nested bootloader/Python process to relinquish the EXE before rollback.
            deadline = time.monotonic() + 10
            while True:
                accounting = Accounting()
                if not api.QueryInformationJobObject(self.job, 1, c.byref(accounting), c.sizeof(accounting), None):
                    raise OSError('无法确认自检子进程已退出')
                if not accounting.active:
                    break
                if time.monotonic() >= deadline:
                    raise OSError('自检子进程未能全部退出')
                time.sleep(.05)
            api.CloseHandle(self.job); self.job = None
        for name in ('thread', 'process'):
            handle = getattr(self.info, name)
            if handle:
                api.CloseHandle(handle); setattr(self.info, name, None)

    def __exit__(self, *args):
        self.close()
