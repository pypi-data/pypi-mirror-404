

import sys
import warnings
import logging

logger = logging.getLogger(__name__)

def enable_unawaited_warning():
    """
    捕获所有未被 await 的协程产生的 RuntimeWarning，
    并用 logger.critical 记录：包括文件名和行号。
    """
    # 原始的 showwarning，用于非 RuntimeWarning 恢复默认行为
    _orig_showwarning = warnings.showwarning

    def _custom_warning_handler(
        message,
        category,
        filename,
        lineno,
        file=None,
        line=None
    ):
        if issubclass(category, RuntimeWarning):
            # 只处理 RuntimeWarning
            logger.critical(f"(File: {filename}, Line: {lineno}) {message}")
        else:
            # 其他警告恢复原来的行为
            _orig_showwarning(message, category, filename, lineno, file, line)

    # 打开协程 origin tracking（需 Python 3.11+）
    sys.set_coroutine_origin_tracking_depth(5)
    # 始终发出 RuntimeWarning
    warnings.simplefilter("always", RuntimeWarning)
    # 覆写全局 showwarning
    warnings.showwarning = _custom_warning_handler
