#!/usr/bin/env python3
"""完整测试：登录 + 获取传感器数据 + 测试新阶梯API"""

import sys
sys.path.insert(0, '.')
import json
import datetime

from csg_client import CSGClient, CSGElectricityAccount, CSGAPIError

def full_test():
    """完整测试流程"""

    print('=' * 70)
    print('HA-Grid-South 集成完整测试')
    print('=' * 70)
    print()

    # 步骤1：创建客户端并发送验证码
    phone = '18313724097'
    client = CSGClient()

    print(f'📱 手机号: {phone}')
    print('🔄 正在发送验证码...')

    try:
        client.api_send_login_sms(phone)
        print('✅ 验证码已发送')
    except Exception as e:
        print(f'❌ 发送验证码失败: {e}')
        return

    # 步骤2：输入验证码
    print()
    code = input('请输入验证码: ').strip()

    if not code:
        print('❌ 验证码不能为空')
        return

    # 步骤3：登录
    print()
    print('🔐 正在登录...')
    try:
        account_numbers = client.login_with_sms_code(phone, code)
        print(f'✅ 登录成功！获取到 {len(account_numbers)} 个账户')
    except Exception as e:
        print(f'❌ 登录失败: {e}')
        return

    # 步骤4：保存session
    with open('session.json', 'w') as f:
        json.dump({
            'account_number': phone,
            'auth_token': client._auth_token,
            'login_type': client._login_type.value if client._login_type else None
        }, f, indent=2)
    print('✅ Session已保存到 session.json')

    # 步骤5：获取账户列表
    print()
    print('=' * 70)
    print('获取账户列表')
    print('=' * 70)

    try:
        accounts_data = client.api_get_all_linked_electricity_accounts()
        print(f'✅ 找到 {len(accounts_data)} 个账户')

        accounts = []
        for acc_data in accounts_data:
            account = CSGElectricityAccount(
                account_number=acc_data.get('accountNumber') or acc_data.get('eleCustNumber'),
                area_code=acc_data.get('areaCode'),
                ele_customer_id=acc_data.get('eleCustId'),
                metering_point_id=acc_data.get('meteringPointId'),
                metering_point_number=acc_data.get('meteringPointNumber'),
                user_name=acc_data.get('userName'),
                address=acc_data.get('address')
            )
            accounts.append(account)
            print(f"  • {account.account_number} - {account.user_name} ({account.address})")

    except Exception as e:
        print(f'❌ 获取账户列表失败: {e}')
        return

    # 步骤6：测试第一个账户的传感器数据
    if not accounts:
        print('❌ 没有可用账户')
        return

    account = accounts[0]
    now = datetime.datetime.now()

    print()
    print('=' * 70)
    print(f'测试账户: {account.account_number} ({account.user_name})')
    print('=' * 70)

    # 测试1：余额和欠费
    print()
    print('📊 测试1: 余额和欠费')
    print('-' * 70)
    try:
        balance, arrears = client.get_balance_and_arrears(account)
        print(f'✅ 账户余额: {balance} CNY')
        print(f'✅ 欠费金额: {arrears} CNY')
    except Exception as e:
        print(f'❌ 失败: {e}')

    # 测试2：昨日用电量
    print()
    print('📊 测试2: 昨日用电量')
    print('-' * 70)
    try:
        yesterday_kwh = client.get_yesterday_kwh(account)
        print(f'✅ 昨日用电量: {yesterday_kwh} kWh')
    except Exception as e:
        print(f'❌ 失败: {e}')

    # 测试3：年度阶梯累计
    print()
    print('📊 测试3: 年度阶梯累计')
    print('-' * 70)
    try:
        yearly_info = client.get_yearly_ladder_info(account, now.year)
        print(f'✅ 年度阶梯累计: {yearly_info["yearly_ladder_total_kwh"]} kWh')
    except Exception as e:
        print(f'❌ 失败: {e}')

    # 测试4：新API - 年度阶梯电价信息 ⭐
    print()
    print('📊 测试4: 新API - 年度阶梯电价信息')
    print('-' * 70)
    try:
        tier_info = client.get_calendar_ladder_info(account, (now.year, now.month))
        print(f'✅ 业务日期: {tier_info.get("business_date")}')
        print(f'✅ 年度累计用电: {tier_info.get("yearly_ladder_total_kwh")} kWh')
        print(f'✅ 当前阶梯: {tier_info.get("ladder")} ({tier_info.get("current_ladder_name")})')
        print(f'✅ 当前电价: {tier_info.get("tariff")} CNY/kWh')
        print(f'✅ 剩余电量: {tier_info.get("remaining_kwh")} kWh')
        print(f'✅ 阶梯起始: {tier_info.get("start_date")}')
        print(f'✅ 阶梯结束: {tier_info.get("ladder_end_date")}')

        # 显示所有阶梯档位
        all_tiers = tier_info.get("all_tiers", [])
        if all_tiers:
            print()
            print(f'📈 所有阶梯档位 (共{len(all_tiers)}个):')
            for i, tier in enumerate(all_tiers, 1):
                print(f'  {i}. {tier["name"]} - {tier["range_min"]}-{tier["range_max"]} kWh @ {tier["price"]} 元/度')

    except Exception as e:
        print(f'❌ 新API失败: {type(e).__name__}: {e}')

    # 测试5：月度数据（主API）
    print()
    print('📊 测试5: 月度数据 (主API)')
    print('-' * 70)
    try:
        month_cost, month_kwh, ladder, by_day = client.get_month_daily_cost_detail(
            account, (now.year, now.month)
        )
        print(f'✅ 本月用电量: {month_kwh} kWh')
        print(f'✅ 本月电费: {month_cost} CNY')
        print(f'✅ 当前阶梯: {ladder.get("ladder")}')
        print(f'✅ 当前电价: {ladder.get("tariff")} CNY/kWh')
        print(f'✅ 剩余电量: {ladder.get("remaining_kwh")} kWh')
        print(f'✅ 每日明细条数: {len(by_day)} 条')
    except CSGAPIError as e:
        print(f'⚠️ 主API失败 (服务器问题): {e}')
    except Exception as e:
        print(f'❌ 其他错误: {type(e).__name__}: {e}')

    # 测试6：年度统计数据
    print()
    print('📊 测试6: 年度统计数据')
    print('-' * 70)
    try:
        year_cost, year_kwh, by_month = client.get_year_month_stats(account, now.year)
        print(f'✅ 本年用电量: {year_kwh} kWh')
        print(f'✅ 本年电费: {year_cost} CNY')
        print(f'✅ 月度数据条数: {len(by_month)} 条')

        # 显示前3个月数据
        if by_month:
            print()
            print('  最近3个月数据:')
            for m in by_month[:3]:
                print(f'    {m.get("month")}: {m.get("kwh")} kWh, {m.get("cost")} CNY')

    except Exception as e:
        print(f'❌ 失败: {e}')

    print()
    print('=' * 70)
    print('✅ 测试完成！')
    print('=' * 70)

if __name__ == '__main__':
    full_test()
