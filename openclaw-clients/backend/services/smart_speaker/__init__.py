# 智能音箱回调处理
from . import tmall_handler
from . import xiaomi_handler
from . import baidu_handler
from .other_handlers import handle_huawei as huawei_handler
from .other_handlers import handle_jd as jd_handler
from .other_handlers import handle_samsung as samsung_handler
from .other_handlers import handle_homekit as homekit_handler

__all__ = [
    'tmall_handler',
    'xiaomi_handler',
    'baidu_handler',
    'huawei_handler',
    'jd_handler',
    'samsung_handler',
    'homekit_handler'
]
