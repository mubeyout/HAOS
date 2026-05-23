#!/usr/bin/env python3
"""发送验证码"""

import sys
sys.path.insert(0, '.')

from csg_client import CSGClient

phone = '18313724097'

client = CSGClient()

print(f'📱 向 {phone} 发送验证码...')

try:
    client.api_send_login_sms(phone)
    print('✅ 验证码已发送')
    print()
    print('请查看手机短信，然后运行:')
    print('  python3 login_and_test.py <验证码>')
except Exception as e:
    print(f'❌ 失败: {e}')
    import traceback
    traceback.print_exc()
