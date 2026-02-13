#!/usr/bin/env python3
"""测试昆仑燃气API"""

import sys
import os

# 添加 gas_client 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'petrochina-gas'))

from gas_client.client import GasHttpClient


def main():
    USER_CODE = "15068622"
    CID = 2
    TERMINAL_TYPE = 7

    print("=" * 60)
    print("昆仑燃气 API 测试")
    print("=" * 60)
    print(f"户号: {USER_CODE}, 地区代码: {CID}")

    client = GasHttpClient(
        user_code=USER_CODE,
        cid=CID,
        terminal_type=TERMINAL_TYPE
    )

    try:
        # 测试余额查询
        print("\n[1] 查询余额...")
        account = client.get_user_debt()
        if account:
            print(f"  账户ID: {account.account_id}")
            print(f"  户号: {account.user_code}")
            print(f"  客户名: {account.customer_name}")
            print(f"  地址: {account.address}")
            print(f"  余额: {account.remote_meter_balance} 元")
            print(f"  MDM代码: {account.mdm_code}")
        else:
            print("  获取失败")

        # 测试阶梯价格
        print("\n[2] 查询阶梯价格...")
        ladder = client.get_ladder_pricing()
        if ladder:
            print(f"  当前阶梯: 第 {ladder.get('current_ladder')} 阶")
            for i in [1, 2, 3]:
                info = ladder.get(f'ladder_{i}')
                if info and info.get('price'):
                    print(f"  第{i}阶梯: {info.get('price')} 元/m3")
        else:
            print("  获取失败")

    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
