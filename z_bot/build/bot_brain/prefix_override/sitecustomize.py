import sys
if sys.prefix == '/home/gautam/.venvs/ros':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/gautam/z_bot/install/bot_brain'
