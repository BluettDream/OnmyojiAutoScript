import threading
from typing import Callable, Optional


class Debouncer:
    """
    防抖器 - 控制函数执行频率

    - 短时间内多次调用 trigger()，只会在最后一次调用后延迟delay执行一次
    """

    def __init__(self, callback: Callable, delay: float = 1.0):
        """
        :param callback: 要执行的保存函数
        :param delay: 延迟时间（秒），默认 1 秒
        """
        self.callback = callback
        self.delay = delay
        self._timer: Optional[threading.Timer] = None
        self._lock = threading.Lock()
        self._last_trigger_time = 0

    def trigger(self):
        """触发保存（会延迟执行）"""
        with self._lock:
            # 取消之前的定时器
            if self._timer is not None and self._timer.is_alive():
                self._timer.cancel()

            # 创建新的定时器
            self._timer = threading.Timer(self.delay, self._execute)
            self._timer.daemon = True  # 设置为守护线程
            self._timer.start()

    def _execute(self):
        """实际执行保存"""
        try:
            self.callback()
        except Exception as e:
            print(f"Error in debounced save: {e}")

    def flush(self):
        """立即执行保存（如果有待执行的）"""
        with self._lock:
            if self._timer is not None and self._timer.is_alive():
                self._timer.cancel()
                self._execute()

    def cancel(self):
        """取消待执行的保存"""
        with self._lock:
            if self._timer is not None and self._timer.is_alive():
                self._timer.cancel()
