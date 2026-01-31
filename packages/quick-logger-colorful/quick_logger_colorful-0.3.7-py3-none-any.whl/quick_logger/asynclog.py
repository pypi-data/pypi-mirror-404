import datetime
import os
import sys
import json
import inspect
import traceback
import asyncio
from functools import wraps  # 保留原函数元信息，关键！

# ===================== 路径与配置初始化 =====================
# 定义路径常量，跨平台兼容
LOG_ROOT = os.path.join(os.getcwd(), "Logs")
CONFIG_DIR = os.path.join(LOG_ROOT, ".config")
CONFIG_PATH = os.path.join(CONFIG_DIR, "Config.json")

# 自动创建目录（简化写法，exist_ok=True 避免重复创建报错）
os.makedirs(LOG_ROOT, exist_ok=True)
os.makedirs(CONFIG_DIR, exist_ok=True)

# 默认配置（把file里的{time}改为{date}，语义更清晰）
DEFAULT_CONF = {
    "pattern": "[{time}][{func}][{type}]:{inform}",
    "file": os.path.join(LOG_ROOT, "{date}.log.txt"),
    "enable_color": True
}

# 初始化配置文件（不存在则创建）
if not os.path.exists(CONFIG_PATH):
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(DEFAULT_CONF, f, indent=4)  # 格式化配置，方便手动修改

# 读取配置
with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
    conf = json.load(f)

# 日志级别控制（-O参数启用生产模式，只显示INFO及以上）
level = 1 if "-O" in sys.argv else 0

# ===================== ANSI颜色配置 =====================
COLORS = {
    "DEBUG": "\033[36m",        # 青色（比灰色醒目）
    "INFO": "\033[32m",         # 绿色
    "WARN": "\033[33m",         # 黄色
    "ERROR": "\033[31m",        # 红色
    "FATAL": "\033[5;41;1;37m"    # 红底白字加粗
}
RESET = "\033[0m"  # 重置颜色，避免终端全局变色

# ===================== 日志核心类 =====================
class Logger(object):
    def __init__(self, pattern=conf["pattern"], file=conf["file"]):
        self.pattern = pattern
        # 按日期命名日志文件（每天一个文件，避免文件过多）
        date_str = datetime.datetime.now().strftime(r"%Y_%m_%d")
        self.file_path = file.format(date=date_str)  # 对应配置里的{date}
        # 追加模式打开，UTF-8编码兼容所有字符（如中文）
        self.file = open(self.file_path, "a", encoding="utf-8")

    def __del__(self):
        """析构函数：程序退出时自动关闭文件，防止句柄泄漏"""
        if hasattr(self, "file") and not self.file.closed:
            self.file.close()

    def _get_real_func_name(self):
        """修复栈帧层级，获取真实的业务函数名（跳过ErrorCatch）"""
        frame = inspect.currentframe()
        # 向上追溯2层：跳过log方法 → 跳过ErrorCatch → 拿到真实函数
        for _ in range(2):
            frame = frame.f_back if frame else None
        func_name = frame.f_code.co_name if frame else "unknown"
        del frame  # 释放栈帧，避免内存泄漏
        return func_name

    async def log(self, data, typ=1):
        type_map = {0: "DEBUG", 1: "INFO", 2: "WARN", 3: "ERROR", 4: "FATAL"}
        log_type = type_map.get(typ, "DEBUG")
        if conf["enable_color"]:
            color=COLORS[log_type]
            rst=RESET
        else:
            color=""
            rst=""
        if typ >= level:
            log_content = self.pattern.format(
                time=datetime.datetime.now().strftime(r"%Y-%m-%d %H:%M:%S"),
                func=self._get_real_func_name(),
                type=log_type,
                inform=data
            )
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, print, f"{color}{log_content}{rst}")
            # 文件输出（使用 run_in_executor 避免阻塞事件循环）
            def write_to_file():
                print(log_content, file=self.file, flush=True)
            await loop.run_in_executor(None, write_to_file)

# ===================== 装饰器（异常捕获器） =====================
def start_logger(func):
    # 每个装饰器创建独立的logger实例（也可改为单例，按需调整）
    logger = Logger()
    
    # 检查是否为协程函数
    if asyncio.iscoroutinefunction(func):
        # 异步函数装饰器
        @wraps(func)
        async def async_ErrorCatch(*args, **kwargs):
            # 注入logger到被装饰函数的局部命名空间
            frame = inspect.currentframe().f_back
            frame.f_locals["logger"] = logger

            try:
                # 执行原协程函数
                return await func(*args, **kwargs)
            except Exception as e:
                # 拼接异常信息（含栈追踪）
                error_info = f"Function [{func.__name__}] error: {str(e)}"
                error_info += f"{RESET}\n{traceback.format_exc()}"
                # 异步记录异常
                await logger.log(error_info, typ=4 if type(e) in [ImportError, SyntaxError, ModuleNotFoundError, OSError, FileNotFoundError, MemoryError, ConnectionRefusedError,
                                                  PermissionError, AssertionError] else 3)
                raise
            finally:
                del frame  # 释放栈帧，避免内存泄漏

        return async_ErrorCatch
    else:
        # 同步函数装饰器（注意：同步函数中使用异步 logger 需要特殊处理）
        @wraps(func)
        def sync_ErrorCatch(*args, **kwargs):
            # 注入logger到被装饰函数的局部命名空间
            frame = inspect.currentframe().f_back
            frame.f_locals["logger"] = logger

            try:
                # 执行原函数
                return func(*args, **kwargs)
            except Exception as e:
                # 拼接异常信息（含栈追踪）
                error_info = f"Function [{func.__name__}] error: {str(e)}"
                error_info += f"{RESET}\n{traceback.format_exc()}"
                # 同步函数中调用异步 log 需要创建事件循环
                try:
                    # 尝试获取运行中的事件循环
                    loop = asyncio.get_running_loop()
                    # 如果有运行中的循环，创建任务（不等待完成）
                    asyncio.create_task(logger.log(error_info, typ=4 if e in [ImportError, SyntaxError, ModuleNotFoundError, OSError, FileNotFoundError, MemoryError, ConnectionRefusedError,
                                                  PermissionError, AssertionError] else 3))
                except RuntimeError:
                    # 没有运行中的事件循环，创建新的并运行
                    asyncio.run(logger.log(error_info, typ=4 if e in [ImportError, SyntaxError, ModuleNotFoundError, OSError, FileNotFoundError, MemoryError, ConnectionRefusedError,
                                                  PermissionError, AssertionError] else 3))
                raise
            finally:
                del frame  # 释放栈帧，避免内存泄漏

        return sync_ErrorCatch

