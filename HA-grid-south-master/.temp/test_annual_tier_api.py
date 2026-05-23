#!/usr/bin/env python3
"""测试新的阶梯电价API"""

import sys
sys.path.insert(0, '.')
import json
import datetime

from csg_client import CSGClient, CSGElectricityAccount

def test_annual_tier_api():
    """测试年度阶梯电价API"""

    # 加载session
    try:
        with open('session.json', 'r') as f:
            session_data = json.load(f)
    except FileNotFoundError:
        print("❌ session.json 不存在，请先登录")
        return

    client = CSGClient()
    client._auth_token = session_data.get('auth_token')
    client._account_number = session_data.get('account_number')

    # 创建账户对象
    account = CSGElectricityAccount(
        account_number='0501133211814158',
        area_code='050100',
        ele_customer_id='gZ04p4NB',
        metering_point_id='c0faf793a8aebebd79ae7357c4456524',
        user_name='周其然',
        address='昆明'
    )

    now = datetime.datetime.now()

    print('=' * 70)
    print('新API测试：api_query_annual_electricity_tier_info')
    print('=' * 70)
    print(f'账户: {account.account_number} ({account.user_name})')
    print(f'查询月份: {now.year}-{now.month:02d}')
    print()

    # 调用新API
    try:
        print('🔄 正在调用新API...')
        result = client.api_query_annual_electricity_tier_info(
            account.area_code,
            account.ele_customer_id,
            account.metering_point_id,
            (now.year, now.month)
        )

        print('✅ 新API调用成功！')
        print()
        print('📊 完整响应数据:')
        print(json.dumps(result, indent=2, ensure_ascii=False))
        print()
        print('📊 解析后的阶梯数据:')
        print(f'  • 业务日期: {result.get("businessDate")}')
        print(f'  • 年度累计用电: {result.get("totalElectricityOfYear")} kWh')
        print(f'  • 当前阶梯: {result.get("currentGear")}')
        print(f'  • 当前电价: {result.get("currentElectricityPrice")} CNY/kWh')
        print(f'  • 剩余电量: {result.get("gearPowerLeft")} kWh')
        print(f'  • 阶梯起始: {result.get("startDate")}')
        print(f'  • 阶梯结束: {result.get("endDate")}')
        print()

        # 显示所有阶梯档位
        ladder_list = result.get("ladderInfoList", [])
        print(f'📈 所有阶梯档位 (共{len(ladder_list)}个):')
        for i, tier in enumerate(ladder_list, 1):
            print(f'  {i}. {tier["ladderName"]}')
            print(f'     范围: {tier["threshholdBottom"]}-{tier["threshholdTop"]} kWh')
            print(f'     电价: {tier["priceValue"]} 元/度')

    except Exception as e:
        print(f'❌ API调用失败: {type(e).__name__}: {e}')
        import traceback
        traceback.print_exc()

    print()
    print('=' * 70)

    # 测试高级封装方法
    print()
    print('=' * 70)
    print('高级方法测试：get_calendar_ladder_info')
    print('=' * 70)
    print()

    try:
        ladder_info = client.get_calendar_ladder_info(account, (now.year, now.month))

        print('✅ 高级方法调用成功！')
        print()
        print('📊 返回的阶梯信息:')
        print(f'  • 当前阶梯档位: {ladder_info.get("ladder")} ({ladder_info.get("current_ladder_name")})')
        print(f'  • 当前阶梯电价: {ladder_info.get("tariff")} CNY/kWh')
        print(f'  • 剩余电量: {ladder_info.get("remaining_kwh")} kWh')
        print(f'  • 年度累计用电: {ladder_info.get("yearly_ladder_total_kwh")} kWh')
        print(f'  • 阶梯起始日期: {ladder_info.get("start_date")}')
        print(f'  • 阶梯结束日期: {ladder_info.get("ladder_end_date")}')

    except Exception as e:
        print(f'❌ 高级方法调用失败: {type(e).__name__}: {e}')
        import traceback
        traceback.print_exc()

    print()
    print('=' * 70)

if __name__ == '__main__':
    test_annual_tier_api()
