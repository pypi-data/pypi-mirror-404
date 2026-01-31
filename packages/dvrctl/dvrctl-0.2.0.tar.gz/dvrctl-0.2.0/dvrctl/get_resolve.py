from .project_manager import *
from .project import *
from .media_storage import *
from .media_pool import *
from .timeline import *
from .general import *
from .deliver import *


class GetResolve:
    def __init__(self, fuscript_path=None, host=None, loglevel='INFO'):
        def __log_print(level, text):
            levels = ["debug", "info", "warning", "error", "critical"]

            try:
                current_idx = levels.index(level.lower())
                threshold_idx = levels.index(loglevel.lower())
            except ValueError:
                # 如果级别无效，默认按 info 处理
                current_idx = 1
                threshold_idx = levels.index(loglevel.lower()) if loglevel.lower() in levels else 1

            # 消息级别 >= 阈值级别 才输出
            if current_idx >= threshold_idx:
                print(f'[dvrctl].[{level.upper()}] - {text}')

        # >>> Get Fusion Script File >>>--------------------------------------------------------------------------------
        import sys
        import os

        def __get_fusionscript():
            # --- 官方加载方法，勿动 ---
            def load_dynamic(module_name, file_path):
                if sys.version_info[0] >= 3 and sys.version_info[1] >= 5:
                    import importlib.machinery
                    import importlib.util

                    module = None
                    spec = None
                    loader = importlib.machinery.ExtensionFileLoader(module_name, file_path)
                    if loader:
                        spec = importlib.util.spec_from_loader(module_name, loader)
                    if spec:
                        module = importlib.util.module_from_spec(spec)
                    if module:
                        loader.exec_module(module)
                    return module
                else:
                    import imp
                    return imp.load_dynamic(module_name, file_path)

            # --- 辅助函数：从环境变量或默认路径获取 ---
            def __get_fallback_path(ext, default_paths):
                """从环境变量或默认路径列表中获取 fusionscript 路径"""
                lib_path = os.getenv("RESOLVE_SCRIPT_LIB")
                if lib_path:
                    path = os.path.join(lib_path, f"fusionscript.{ext}")
                    __log_print('debug', f"Found RESOLVE_SCRIPT_LIB: {path}")
                    return path

                # 尝试默认路径列表
                for path in default_paths:
                    if os.path.exists(path):
                        __log_print('info', f"Using existing default path: {path}")
                        return path

                # 返回第一个默认路径（即使不存在）
                __log_print('info', f"Using default path: {default_paths[0]}")
                return default_paths[0]

            # --- 1. 如果 globals 里已经有 bmd，就直接用 ---
            try:
                if 'bmd' in globals():
                    __log_print('debug', "Using bmd from globals()")
                    return globals()['bmd']
                elif 'bmd' in globals()['__builtins__']:
                    __log_print('debug', "Using bmd from __builtins__")
                    return globals()['__builtins__']['bmd']
            except Exception as e:
                __log_print('warning', f"Error checking globals: {e}")

            # --- 2. 如果有命令行参数，解析并优先使用 ---
            if fuscript_path:
                if os.path.exists(fuscript_path):
                    __log_print('debug', f"Using fusionscript from argument: {fuscript_path}")
                    return load_dynamic("fusionscript", fuscript_path)
                else:
                    raise FileNotFoundError(f"Invalid fusionscript path from arguments: {fuscript_path}")

            # --- 3. 自动探测 ---
            fusionscript_path = None

            if sys.platform.startswith("darwin"):
                import subprocess
                try:
                    pid = subprocess.check_output(
                        "pgrep -x Resolve",
                        shell=True,
                        text=True
                    ).splitlines()[0].strip()

                    cmd = f"lsof -F n -p {pid} -a -d txt | grep 'fusionscript.so$' | sed 's/^n//'"
                    fusionscript_path = subprocess.check_output(cmd, shell=True, text=True).strip()
                    __log_print('debug', f"Found fusionscript via process: {fusionscript_path}")

                except subprocess.CalledProcessError:
                    __log_print('warning', "Could not find Resolve process, trying RESOLVE_SCRIPT_LIB env...")
                    fusionscript_path = __get_fallback_path("so", [
                        "/Applications/DaVinci Resolve/DaVinci Resolve.app/Contents/Libraries/Fusion/fusionscript.so"
                    ])

            elif sys.platform.startswith("win"):
                import psutil

                for proc in psutil.process_iter(['pid', 'name', 'exe']):
                    try:
                        if 'Resolve' in proc.info['name']:
                            resolve_exe_path = proc.info['exe']
                            fusionscript_path = os.path.join(
                                os.path.dirname(resolve_exe_path),
                                "fusionscript.dll"
                            )
                            if os.path.exists(fusionscript_path):
                                __log_print('debug', f"Found fusionscript via process: {fusionscript_path}")
                                break
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue

                if not fusionscript_path:
                    __log_print('warning', "Could not find Resolve process, trying RESOLVE_SCRIPT_LIB env...")
                    fusionscript_path = __get_fallback_path("dll", [
                        "C:\\Program Files\\Blackmagic Design\\DaVinci Resolve\\fusionscript.dll"
                    ])

            elif sys.platform.startswith("linux"):
                import subprocess

                try:
                    # 合并两个路径的查找
                    pids = subprocess.check_output(
                        "ps -eo pid,cmd | grep -E '/(opt|home)/resolve/bin/resolve' | grep -v grep | awk '{print $1}'",
                        shell=True,
                        text=True
                    ).strip().splitlines()

                    if pids:
                        pid = pids[0]
                        cmd = f"lsof -p {pid} -Fn | grep fusionscript.so | sed 's/^n//'"
                        fusionscript_path = subprocess.check_output(cmd, shell=True, text=True).strip()
                        __log_print('debug', f"Found fusionscript via process: {fusionscript_path}")

                except subprocess.CalledProcessError:
                    __log_print('warning', "Could not find Resolve process")

                if not fusionscript_path:
                    __log_print('warning', "Trying RESOLVE_SCRIPT_LIB env...")
                    fusionscript_path = __get_fallback_path("so", [
                        "/opt/resolve/libs/Fusion/fusionscript.so",
                        "/home/resolve/libs/Fusion/fusionscript.so"
                    ])

            else:
                raise OSError(f"Unsupported platform: {sys.platform}")

            # --- 4. 加载 fusionscript ---
            if fusionscript_path and os.path.exists(fusionscript_path):
                try:
                    __log_print('debug', f"Loading fusionscript from: {fusionscript_path}")
                    return load_dynamic("fusionscript", fusionscript_path)
                except Exception as e:
                    raise RuntimeError(f"Failed to load fusionscript: {e}")
            else:
                raise FileNotFoundError(
                    f"Could not find fusionscript at: {fusionscript_path or 'unknown path'}"
                )

        # <<< Get Fusion Script File <<<--------------------------------------------------------------------------------

        # >>> Link DaVinci >>>------------------------------------------------------------------------------------------
        fusionscript = __get_fusionscript()

        if host:
            ask_continue = input(f'The script affects on {host}, Continue?(y/n):')
            if ask_continue.lower() != 'y':  # 改进：不区分大小写
                raise SystemExit("User cancelled operation")

            self.resolve = fusionscript.scriptapp('Resolve', host)
            if self.resolve is None:
                raise RuntimeError(f'\033[1;31mHost {host} not available\033[0m')
        else:
            self.resolve = fusionscript.scriptapp('Resolve')

        if self.resolve is None:
            __log_print('error', '\033[1;31mDaVinci Resolve not running or not accessible\033[0m')
            raise RuntimeError('DaVinci Resolve not running or not accessible')

        __log_print('debug', 'Successfully connected to DaVinci Resolve')
        # <<< Link DaVinci <<<------------------------------------------------------------------------------------------

    def __getattr__(self, name):
        """让没有在包装类中定义的属性，直接去内部对象找"""
        return getattr(self.resolve, name)

    def __repr__(self):
        """print 时，显示内部对象的 repr"""
        return repr(self.resolve)

    # >>> Individual components >>>-------------------------------------------------------------------------------------
    def pjm(self):
        return ProjectManager(self.resolve)

    def pj(self):
        return Project(self.resolve)

    def mds(self):
        return MediaStorage(self.resolve)

    def mdp(self):
        return MediaPool(self.resolve)

    def tl(self):
        return Timeline(self.resolve)

    def general(self):
        return General(self.resolve)

    def deliver(self):
        return Deliver(self.resolve)
    # <<< Individual components <<<-------------------------------------------------------------------------------------
