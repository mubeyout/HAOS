#!/usr/bin/env python3
"""测试方法1：电费日历API"""

import sys
sys.path.insert(0, '.')
import json
import datetime

from csg_client import CSGClient, CSGElectricityAccount

def test_method_1():
    """测试方法1：直接调用电费日历API"""

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
        ele_customer_id='plQkqxFW',
        metering_point_id='fc3c1d235e3d761951472bb874a19724',
        user_name='周其然',
        address='昆明'
    )

    now = datetime.datetime.now()

    print('=' * 70)
    print('方法1：电费日历API测试 (api_query_day_electric_charge_by_m_point)')
    print('=' * 70)
    print(f'测试时间: {now.strftime("%Y-%m-%d %H:%M:%S")}')
    print(f'账户: {account.account_number} ({account.user_name})')
    print(f'测试月份: {now.year}-{now.month:02d}')
    print(f'地区代码: {account.area_code}')
    print(f'客户ID: {account.ele_customer_id}')
    print(f'计量点ID: {account.metering_point_id}')
    print('-' * 70)

    # 方法1：调用主API
    try:
        print('\n🔄 正在调用主API...')
        result = client.api_query_day_electric_charge_by_m_point(
            now.year,
            now.month,
            account.area_code,
            account.ele_customer_id,
            account.metering_point_id
        )

        print('✅ 方法1成功！API返回完整数据')
        print()
        print('📊 阶梯数据 (从API直接获取):')
        print(f'  • 当前阶梯档位: {result.get("ladderEle")}')
        print(f'  • 当前阶梯电价: {result.get("ladderEleTariff")} CNY/kWh')
        print(f'  • 剩余电量: {result.get("ladderEleSurplus")} kWh')
        print(f'  • 阶梯起始日期: {result.get("ladderEleStartDate")}')
        print()
        print('📈 月度汇总:')
        print(f'  • 总用电量: {result.get("totalPower")} kWh')
        print(f'  • 总电费: {result.get("totalElectricity")} CNY')
        print()
        print(f'📅 每日明细数据: {len(result.get("result", []))} 条')

        # 显示前3条数据
        daily_data = result.get("result", [])
        if daily_data:
            print('\n每日数据示例 (前3条):')
            for i, day in enumerate(daily_data[:3], 1):
                print(f'  {i}. {day.get("date")}: {day.get("power")} kWh, {day.get("charge")} CNY')

        # 计算验证
        if result.get("totalPower") and result.get("ladderEleTariff"):
            calculated_cost = round(float(result["totalPower"]) * float(result["ladderEleTariff"]), 2)
            actual_cost = float(result.get("totalElectricity", 0))
            print(f'\n💡 费用计算验证:')
            print(f'  • 计算: {result["totalPower"]} × {result["ladderEleTariff"]} = {calculated_cost} CNY')
            print(f'  • 实际: {actual_cost} CNY')
            if abs(calculated_cost - actual_cost) < 0.1:
                print(f'  • 状态: ✅ 验证通过')

    except Exception as e:
        print(f'⚠️ 方法1失败: {e}')
        print()
        print('🔄 降级到方法2...')

        # 方法2：年度统计API
        try:
            result2 = client.api_get_fee_analyze_details(
                now.year,
                account.area_code,
                account.ele_customer_id
            )

            print('✅ 方法2成功')
            print(f'  • 年度总用电: {result2.get("totalBillingElectricity")} kWh')
            print(f'  • 年度总费用: {result2.get("totalActualAmount")} CNY')

            # 月度数据
            monthly_list = result2.get("electricAndChargeList", [])
            print(f'\n📅 月度数据条数: {len(monthly_list)}')

            # 查找当前月
            for m in monthly_list:
                if m.get("yearMonth") == f"{now.year}-{now.month:02d}":
                    print(f'\n{now.year}年{now.month}月数据:')
                    print(f'  • 用电量: {m.get("billingElectricity")} kWh')
                    print(f'  • 电费: {m.get("actualTotalAmount")} CNY')
                    break

        except Exception as e2:
            print(f'❌ 方法2也失败: {e2}')

    print()
    print('=' * 70)

if __name__ == '__main__':
    test_method_1()
