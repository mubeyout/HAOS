#!/usr/bin/env python3
"""
HA-Grid-South 传感器数据测试脚本 (非交互式版本)
使用命令行参数传递验证码
"""

import datetime
import json
import os
import sys
import time

# 添加当前目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from csg_client import (
    CSGClient,
    CSGElectricityAccount,
    LoginType,
)

# ============== 配置区 ==============
PHONE_NUMBER = "18313724097"
# ======================================


def print_header(title: str):
    """打印标题"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_sensor(name: str, value: any, unit: str = ""):
    """打印传感器数据"""
    if value is None:
        value = "N/A"
    if unit:
        print(f"  {name:40s}: {value:>10} {unit}")
    else:
        print(f"  {name:40s}: {value}")


def print_sub_header(title: str):
    """打印子标题"""
    print(f"\n--- {title} ---")


def test_login_with_sms(sms_code: str) -> CSGClient:
    """使用短信验证码登录"""
    print_header("步骤 1: 登录南网电网")

    client = CSGClient()

    print(f"\n📱 手机号: {PHONE_NUMBER}")
    print(f"\n🔐 验证码: {sms_code}")
    print("\n正在验证登录...")

    try:
        auth_token = client.api_login_with_sms_code(PHONE_NUMBER, sms_code)
        client.set_authentication_params(auth_token)
        print("✅ 登录成功！")
    except Exception as e:
        print(f"❌ 登录失败: {e}")
        print("\n可能的原因:")
        print("  1. 验证码错误")
        print("  2. 验证码已过期")
        print("  3. 验证码使用次数已达上限")
        sys.exit(1)

    # 初始化客户端
    client.initialize()

    # 保存 session
    session = client.dump()
    with open("session.json", "w", encoding="utf-8") as f:
        json.dump(session, f, ensure_ascii=False, indent=2)
    print("✅ 登录态已保存到 session.json")

    return client


def get_user_info(client: CSGClient):
    """获取用户信息"""
    print_header("步骤 2: 获取用户信息")

    try:
        user_info = client.api_get_user_info()
        print(f"\n  用户手机号: {user_info.get('phone', 'N/A')}")
        print(f"  用户状态: {user_info.get('status', 'N/A')}")
        print(f"  认证状态: {user_info.get('authStatus', 'N/A')}")
    except Exception as e:
        print(f"❌ 获取用户信息失败: {e}")


def list_accounts(client: CSGClient) -> list[CSGElectricityAccount]:
    """列出所有电费账户"""
    print_header("步骤 3: 获取电费账户列表")

    try:
        accounts = client.get_all_electricity_accounts()
        print(f"\n✅ 共找到 {len(accounts)} 个绑定的电费账户\n")

        for i, account in enumerate(accounts):
            print(f"  账户 {i + 1}:")
            print(f"    户号: {account.account_number}")
            print(f"    户名: {account.user_name}")
            print(f"    地址: {account.address}")
            print(f"    客户ID: {account.ele_customer_id}")
            print(f"    计量点ID: {account.metering_point_id}")
            print(f"    地区代码: {account.area_code}")
            print()

        return accounts
    except Exception as e:
        print(f"❌ 获取账户列表失败: {e}")
        return []


def test_account_sensors(client: CSGClient, account: CSGElectricityAccount, account_index: int):
    """测试单个账户的所有传感器"""
    print_header(f"步骤 4.{account_index}: 测试账户传感器数据")
    print(f"户号: {account.account_number}")
    print(f"户名: {account.user_name}")
    print(f"地址: {account.address}")

    now = datetime.datetime.now()
    this_year = now.year
    this_month = now.month

    # ============ 余额和欠费 ============
    print_sub_header("1. 余额和欠费")
    try:
        balance, arrears = client.get_balance_and_arrears(account)
        print_sensor("账户余额 (balance)", f"{balance:.2f}", "CNY")
        print_sensor("欠费金额 (arrears)", f"{arrears:.2f}", "CNY")
    except Exception as e:
        print(f"  ❌ 获取余额失败: {e}")

    # ============ 昨日用电量 ============
    print_sub_header("2. 昨日用电量")
    try:
        yesterday_kwh = client.get_yesterday_kwh(account)
        print_sensor("昨日用电量 (yesterday_kwh)", f"{yesterday_kwh:.2f}", "kWh")
    except Exception as e:
        print(f"  ❌ 获取昨日用电量失败: {e}")

    # ============ 本月用电数据和阶梯信息 ============
    print_sub_header("3. 本月用电数据和阶梯信息")
    try:
        month_total_cost, month_total_kwh, ladder, by_day = client.get_month_daily_cost_detail(
            account, (this_year, this_month)
        )

        # 阶梯信息
        if ladder:
            print(f"\n  【当前阶梯信息】")
            current_ladder = ladder.get("ladder")
            ladder_names = {1: "电能替代", 2: "居民阶梯一", 3: "居民阶梯二", 4: "居民阶梯三"}
            ladder_name = ladder_names.get(current_ladder, f"阶梯{current_ladder}")
            print_sensor("当前阶梯 (current_ladder)", ladder_name)
            print_sensor("当前阶梯电价 (current_ladder_tariff)",
                        f"{ladder.get('tariff', 0):.4f}", "CNY/kWh")
            print_sensor("距下一阶梯电量 (current_ladder_remaining_kwh)",
                        f"{ladder.get('remaining_kwh', 0):.2f}", "kWh")
            print_sensor("阶梯起始日期 (current_ladder_start_date)",
                        ladder.get("start_date", "N/A"))

        print(f"\n  【本月汇总】")
        print_sensor("本月用电量 (this_month_total_usage)", f"{month_total_kwh:.2f}", "kWh")
        print_sensor("本月电费 (this_month_total_cost)", f"{month_total_cost:.2f}", "CNY")

        # 最新一日数据
        if by_day and len(by_day) > 0:
            latest_day = by_day[-1]
            print(f"\n  【最新日数据】 ({latest_day.get('date', 'N/A')})")
            print_sensor("最新日用电量 (latest_day_kwh)",
                        f"{latest_day.get('kwh', 0):.2f}", "kWh")
            print_sensor("最新日电费 (latest_day_cost)",
                        f"{latest_day.get('charge', 0):.2f}", "CNY")

    except Exception as e:
        print(f"  ❌ 获取本月数据失败: {e}")

    # ============ 上月数据 ============
    print_sub_header("4. 上月数据")
    try:
        last_month = this_month - 1 if this_month > 1 else 12
        last_year = this_year if this_month > 1 else this_year - 1
        last_month_cost, last_month_kwh, _, _ = client.get_month_daily_cost_detail(
            account, (last_year, last_month)
        )
        print_sensor("上月用电量 (last_month_total_usage)", f"{last_month_kwh:.2f}", "kWh")
        print_sensor("上月电费 (last_month_total_cost)", f"{last_month_cost:.2f}", "CNY")
    except Exception as e:
        print(f"  ❌ 获取上月数据失败: {e}")

    # ============ 本年数据 ============
    print_sub_header("5. 本年数据")
    try:
        year_charge, year_kwh, by_month = client.get_year_month_stats(account, this_year)
        print_sensor("本年用电量 (this_year_total_usage)", f"{year_kwh:.2f}", "kWh")
        print_sensor("本年电费 (this_year_total_cost)", f"{year_charge:.2f}", "CNY")

        # 月度数据列表
        if by_month and len(by_month) > 0:
            print(f"\n  【本年月度数据】")
            print(f"  {'月份':<10} {'用电量(kWh)':<15} {'电费(CNY)':<15}")
            print(f"  {'-'*40}")
            for m in by_month:
                month_str = m.get('month', '')
                kwh = m.get('kwh', 0)
                charge = m.get('charge', 0)
                print(f"  {month_str:<10} {kwh:>10.2f}       {charge:>10.2f}")
    except Exception as e:
        print(f"  ❌ 获取本年数据失败: {e}")

    # ============ 年度阶梯累计（新增传感器）============
    print_sub_header("6. 年度阶梯累计 (yearly_ladder_total_kwh) ⭐")
    try:
        yearly_ladder_info = client.get_yearly_ladder_info(account, this_year)
        yearly_ladder_kwh = yearly_ladder_info.get("yearly_ladder_total_kwh", 0)
        print_sensor("年度阶梯累计 (yearly_ladder_total_kwh)", f"{yearly_ladder_kwh:.2f}", "kWh")
        print(f"  💡 用途: 用于阶梯电价计算参考，与 this_year_total_usage 数值相同但用途不同")
    except Exception as e:
        print(f"  ❌ 获取年度阶梯累计失败: {e}")

    # ============ 去年数据 ============
    print_sub_header("7. 去年数据")
    try:
        last_year = this_year - 1
        last_year_charge, last_year_kwh, _ = client.get_year_month_stats(account, last_year)
        print_sensor("去年用电量 (last_year_total_usage)", f"{last_year_kwh:.2f}", "kWh")
        print_sensor("去年电费 (last_year_total_cost)", f"{last_year_charge:.2f}", "CNY")
    except Exception as e:
        print(f"  ❌ 获取去年数据失败: {e}")


def main():
    """主函数"""
    # 检查命令行参数
    if len(sys.argv) < 2:
        print("\n" + "█" * 60)
        print("█" + " " * 15 + "HA-Grid-South 传感器测试" + " " * 17 + "█")
        print("█" * 60)
        print("\n使用方法:")
        print("  python3 test_sensors_cli.py <验证码>")
        print("\n示例:")
        print("  python3 test_sensors_cli.py 123456")
        print("\n或者先发送验证码:")
        print("  python3 send_sms.py")
        print("█" * 60)
        sys.exit(1)

    sms_code = sys.argv[1]

    # 验证验证码格式
    if not sms_code.isdigit() or len(sms_code) != 6:
        print("❌ 验证码必须是 6 位数字！")
        sys.exit(1)

    print("\n" + "█" * 60)
    print("█" + " " * 18 + "HA-Grid-South 传感器测试" + " " * 19 + "█")
    print("█" * 60)

    # 尝试加载已保存的 session
    if os.path.isfile("session.json"):
        print("\n⚠️  检测到已保存的 session.json")
        print("⏭️  跳过登录，使用已保存的登录态...")
        try:
            with open("session.json", encoding="utf-8") as f:
                session_data = json.load(f)
            client = CSGClient.load(session_data)
            client.initialize()

            # 验证登录状态
            if client.verify_login():
                print("✅ 已保存的登录态有效！")
            else:
                print("❌ 已保存的登录态已失效，使用新验证码重新登录...")
                client = test_login_with_sms(sms_code)
        except Exception as e:
            print(f"❌ 加载 session 失败: {e}")
            print("\n使用新验证码重新登录...")
            client = test_login_with_sms(sms_code)
    else:
        client = test_login_with_sms(sms_code)

    # 获取用户信息
    get_user_info(client)

    # 获取账户列表
    accounts = list_accounts(client)

    if not accounts:
        print("\n❌ 没有找到任何电费账户，无法继续测试传感器")
        return

    # 测试每个账户的传感器数据
    for i, account in enumerate(accounts):
        test_account_sensors(client, account, i + 1)
        time.sleep(1)  # 避免请求过快

    # 总结
    print_header("测试完成")
    print(f"\n✅ 共测试 {len(accounts)} 个账户")
    print(f"✅ 每个账户 19 个传感器（共 {len(accounts) * 19} 个传感器实体）")
    print("\n传感器实体ID格式:")
    print("  sensor.china_southern_power_grid_stat_{户号}_{传感器后缀}")
    print("\n示例:")
    print(f"  sensor.china_southern_power_grid_stat_{accounts[0].account_number}_balance")
    print(f"  sensor.china_southern_power_grid_stat_{accounts[0].account_number}_current_ladder")
    print(f"  sensor.china_southern_power_grid_stat_{accounts[0].account_number}_this_month_total_cost")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  测试已中断")
    except Exception as e:
        print(f"\n\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
