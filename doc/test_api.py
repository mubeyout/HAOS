#!/usr/bin/env python3
"""测试昆仑燃气API，获取并展示所有可用数据"""

import sys
import os

# 添加 gas_client 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'petrochina-gas'))

from gas_client.client import GasHttpClient
import json


def print_section(title):
    """打印分隔线"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def main():
    """主测试函数"""
    # 配置参数（请修改为你的实际户号）
    USER_CODE = "15068622"  # 8位数字户号
    CID = 2
    TERMINAL_TYPE = 7

    print(f"""
╔══════════════════════════════════════════════════════════╗
║          昆仑燃气 API 数据获取测试                          ║
╚════════════════════════════════════════════════════════╝

📋 配置参数:
   户号 (userCode): {USER_CODE}
   地区代码 (cid): {CID}
   终端类型 (terminalType): {TERMINAL_TYPE}
""")

    # 创建客户端
    client = GasHttpClient(
        user_code=USER_CODE,
        cid=CID,
        terminal_type=TERMINAL_TYPE
    )

    try:
        # ========================================
        # 1. 查询用户基本信息和余额
        # ========================================
        print_section("1. 用户基本信息 & 余额")

        account = client.get_user_debt()
        if account:
            print(f"✅ 账户ID: {account.account_id}")
            print(f"✅ 户号: {account.user_code}")
            print(f"✅ 客户姓名: {account.customer_name}")
            print(f"✅ 安装地址: {account.address}")
            print(f"✅ 表计类型: {account.meter_type}")
            print(f"✅ MDM代码: {account.mdm_code}")
            print(f"\n💰 余额信息:")
            print(f"   表端余额: {account.remote_meter_balance} 元")
            print(f"\n⏰ 时间信息:")
            print(f"   最近读表时间: {account.reading_last_time}")
            print(f"   最近通讯时间: {account.remote_meter_last_communication_time}")

        # ========================================
        # 2. 查询表计读数历史
        # ========================================
        print_section("2. 表计读数历史（最近10天）")

        readings = client.get_meter_reading(days=10)
        if readings:
            print(f"📊 获取到 {len(readings)} 条记录:\n")
            print(f"{'日期':<20} {'余额':<12} {'用量(m³)':<12} {'费用(元)':<10}")
            print("-" * 60)
            for r in readings[-5:]:  # 只显示最近5条
                print(f"{r['date']:<20} {r['reading']:<12.2f} {r['volume']:<12.2f} {r['cost']:<10.2f}")

        # ========================================
        # 3. 查询每日用气量统计
        # ========================================
        print_section("3. 每日用气量统计（最近30天）")

        usage = client.get_daily_usage(days=30)
        if usage:
            daily_records = usage.get('daily_volumes', [])
            print(f"📈 统计概览:")
            print(f"   记录天数: {len(daily_records)} 天")
            print(f"   总用气量: {usage.get('total_volume', 0):.2f} m³")
            print(f"   总费用: {usage.get('total_cost', 0):.2f} 元")

            if daily_records:
                print(f"\n📅 最近5天记录:")
                print(f"{'日期':<12} {'用量(m³)':<12} {'费用(元)':<10}")
                print("-" * 40)
                for r in daily_records[-5:]:
                    print(f"{r['date']:<12} {r['volume']:<12.2f} {r['cost']:<10.2f}")

        # ========================================
        # 4. 查询阶梯价格
        # ========================================
        print_section("4. 阶梯价格信息")

        ladder = client.get_ladder_pricing()
        if ladder:
            print(f"📊 当前阶梯: 第 {ladder.get('current_ladder')} 阶")
            print(f"\n💰 阶梯价格配置:")
            for i in [1, 2, 3]:
                ladder_info = ladder.get(f'ladder_{i}')
                price = ladder_info.get('price')
                start = ladder_info.get('start')
                end = ladder_info.get('end')
                if price is not None:
                    print(f"   第{i}阶梯: {price} 元/m³ ({start}-{end} m³)")
                else:
                    print(f"   第{i}阶梯: 暂无数据")

        # ========================================
        # 5. 数据汇总（传感器映射）
        # ========================================
        print_section("5. Home Assistant 传感器数据映射")

        print("""
📦 将创建以下 18 个传感器:

┌─────────────────────────────────────────────────────────────────┐
│ 传感器名称                          │ 状态值/单位          │
├─────────────────────────────────────────────────────────────────┤
│ 1. 表端余额                        │ {} 元 │
│ 2. 所属燃气公司                      │ 云南中石油昆仑燃气... │
│ 3. 户号                            │ {} │
│ 4. 用户名                          │ {} │
│ 5. 地址                            │ {} │
│ 6. 最近表读数                      │ {} │
│ 7. 最近通讯时间                    │ {} │
│ 8. 待上表金额                      │ 暂无数据 │
│ 9. 上次缴费金额与时间              │ 暂无数据 │
│ 10. 今日用气量                     │ 暂无数据 │
│ 11. 今日费用                       │ 暂无数据 │
│ 12. 上月用气量                     │ 暂无数据 │
│ 13. 上月费用                       │ 暂无数据 │
│ 14. 近10天/30天用量                │ 暂无数据 │
│ 15. 今年用气量与金额              │ 暂无数据 │
│ 16. 当前阶梯                       │ {} │
│ 17. 阶梯价格                      │ 暂无数据 │
│ 18. 当前所属阶梯与单价             │ 暂无数据 │
└─────────────────────────────────────────────────────────────────┘
        """.format(
            f"{account.remote_meter_balance:.2f}" if account else "N/A",
            account.user_code if account else "N/A",
            account.customer_name if account else "N/A",
            (account.address[:30] + "..." if account and len(account.address) > 30 else account.address) if account else "N/A",
            account.reading_last_time if account else "N/A",
            account.remote_meter_last_communication_time if account else "N/A",
            ladder.get('current_ladder') if ladder else "N/A",
        )

        # ========================================
        # 6. 警告和建议
        # ========================================
        print_section("数据获取状态")

        warnings = []
        if account:
            if account.remote_meter_balance < 30:
                warnings.append(f"🔔 余额偏低！当前 {account.remote_meter_balance} 元，建议及时充值")

        if warnings:
            for w in warnings:
                print(w)
        else:
            print("✅ 所有数据正常")

        print("\n" + "=" * 60)
        print(" 测试完成")
        print("=" * 60 + "\n")

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()

    finally:
        client.close()


if __name__ == "__main__":
    main()
