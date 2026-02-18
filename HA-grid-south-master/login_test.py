#!/usr/bin/env python3
"""登录并测试所有传感器"""

import sys
sys.path.insert(0, '.')

import json
import datetime
from csg_client import CSGClient, CSGElectricityAccount, CSGAPIError

phone = '18313724097'
code = '411584'

print('=' * 70)
print('HA-Grid-South 传感器完整测试')
print('=' * 70)
print(f'手机号: {phone}')
print(f'验证码: {code}')
print()

# 创建客户端并登录
client = CSGClient()

print('🔐 正在登录...')
try:
    auth_token = client.api_login_with_sms_code(phone, code)
    client.auth_token = auth_token
    print(f'✅ 登录成功！')
    print(f'   Token: {auth_token[:20]}...')
except Exception as e:
    print(f'❌ 登录失败: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 保存session
with open('session.json', 'w') as f:
    json.dump({
        'account_number': phone,
        'auth_token': client.auth_token,
    }, f, indent=2)
print('✅ Session已保存')
print()

# 获取账户列表
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
        print(f"  • {account.account_number} - {account.user_name}")

except Exception as e:
    print(f'❌ 获取账户列表失败: {e}')
    sys.exit(1)

if not accounts:
    print('❌ 没有可用账户')
    sys.exit(1)

# 测试第一个账户
account = accounts[0]
now = datetime.datetime.now()

print()
print('=' * 70)
print(f'测试账户: {account.account_number} ({account.user_name})')
print('=' * 70)
print()

results = {}

# 1. 余额和欠费
print('📊 [1/11] 账户余额 (balance)')
try:
    balance, arrears = client.get_balance_and_arrears(account)
    print(f'   ✅ {balance} CNY')
    results['balance'] = balance
except Exception as e:
    print(f'   ❌ {e}')
    results['balance'] = None

print('📊 [2/11] 欠费金额 (arrears)')
try:
    print(f'   ✅ {arrears} CNY')
    results['arrears'] = arrears
except Exception as e:
    print(f'   ❌ {e}')
    results['arrears'] = None

# 2. 昨日用电量
print()
print('📊 [3/11] 昨日用电量 (yesterday_kwh)')
try:
    yesterday_kwh = client.get_yesterday_kwh(account)
    print(f'   ✅ {yesterday_kwh} kWh')
    results['yesterday_kwh'] = yesterday_kwh
except Exception as e:
    print(f'   ❌ {e}')
    results['yesterday_kwh'] = None

# 3. ⭐ 新API - 年度阶梯电价信息
print()
print('📊 [新API] 年度阶梯电价信息')
print('-' * 70)
try:
    tier_info = client.get_calendar_ladder_info(account, (now.year, now.month))
    print(f'   ✅ 业务日期: {tier_info.get("business_date")}')
    print(f'   ✅ 年度累计: {tier_info.get("yearly_ladder_total_kwh")} kWh')
    print(f'   ✅ 当前阶梯: {tier_info.get("ladder")} ({tier_info.get("current_ladder_name")})')
    print(f'   ✅ 当前电价: {tier_info.get("tariff")} CNY/kWh')
    print(f'   ✅ 剩余电量: {tier_info.get("remaining_kwh")} kWh')
    print(f'   ✅ 阶梯期间: {tier_info.get("start_date")} ~ {tier_info.get("ladder_end_date")}')

    results['current_ladder'] = tier_info.get('ladder')
    results['current_ladder_tariff'] = tier_info.get('tariff')
    results['current_ladder_remaining_kwh'] = tier_info.get('remaining_kwh')
    results['yearly_ladder_total_kwh'] = tier_info.get('yearly_ladder_total_kwh')

    all_tiers = tier_info.get('all_tiers', [])
    if all_tiers:
        print()
        print('   📈 所有阶梯档位:')
        for i, tier in enumerate(all_tiers, 1):
            print(f'      {i}. {tier["name"]}: {tier["range_min"]}-{tier["range_max"]} kWh @ {tier["price"]} 元/度')

except Exception as e:
    print(f'   ❌ 新API失败: {type(e).__name__}: {e}')
    import traceback
    traceback.print_exc()
    results['current_ladder'] = None
    results['current_ladder_tariff'] = None
    results['current_ladder_remaining_kwh'] = None

# 4. 月度数据（主API）
print()
print('📊 [主API] 月度数据')
print('-' * 70)
print('📊 [8/11] 本月用电量 (this_month_total_usage)')
print('📊 [9/11] 本月电费 (this_month_total_cost)')
try:
    month_cost, month_kwh, ladder, by_day = client.get_month_daily_cost_detail(
        account, (now.year, now.month)
    )
    print(f'   ✅ 本月用电量: {month_kwh} kWh')
    print(f'   ✅ 本月电费: {month_cost} CNY')
    print(f'   ✅ 每日明细: {len(by_day)} 条')
    results['this_month_total_usage'] = month_kwh
    results['this_month_total_cost'] = month_cost
except CSGAPIError as e:
    print(f'   ⚠️ 主API失败 (服务器问题): {e}')
    results['this_month_total_usage'] = None
    results['this_month_total_cost'] = None
except Exception as e:
    print(f'   ❌ 其他错误: {e}')
    results['this_month_total_usage'] = None
    results['this_month_total_cost'] = None

# 5. 年度统计数据
print()
print('📊 [年度统计] 本年账单数据')
print('-' * 70)
print('📊 [10/11] 本年账单用电量 (this_year_bill_usage)')
print('📊 [11/11] 本年账单费用 (this_year_bill_cost)')
try:
    year_cost, year_kwh, by_month = client.get_year_month_stats(account, now.year)
    print(f'   ✅ 本年用电量: {year_kwh} kWh')
    print(f'   ✅ 本年电费: {year_cost} CNY')
    print(f'   ✅ 月度数据: {len(by_month)} 条')
    results['this_year_bill_usage'] = year_kwh
    results['this_year_bill_cost'] = year_cost
except Exception as e:
    print(f'   ❌ 失败: {e}')
    results['this_year_bill_usage'] = None
    results['this_year_bill_cost'] = None

# 总结
print()
print('=' * 70)
print('✅ 测试完成！传感器数据汇总:')
print('=' * 70)
print()
for key, value in results.items():
    if value is not None:
        print(f'  ✅ {key}: {value}')
    else:
        print(f'  ❌ {key}: 获取失败')
