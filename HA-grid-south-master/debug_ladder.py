#!/usr/bin/env python3
"""
阶梯电价调试脚本
用于检查 API 返回的阶梯数据结构
"""

import json
import sys
from datetime import datetime

# 模拟 API 返回的数据结构示例
EXAMPLE_API_RESPONSE = {
    "sta": "00",
    "data": {
        "result": [
            {"date": "2026-02-01", "power": "5.2", "charge": "1.87"},
            {"date": "2026-02-02", "power": "6.1", "charge": "2.19"},
        ],
        "totalPower": "131.00",
        "totalElectricity": "47.08",
        # 阶梯数据 - 这些字段可能为 null
        "ladderEle": "0",           # 阶梯档位: 0=电能替代, 1=阶梯一, 2=阶梯二, 3=阶梯三
        "ladderEleTariff": "0.3595",  # 当前阶梯电价
        "ladderEleSurplus": "1429.00", # 当前阶梯剩余电量
        "ladderEleStartDate": "2026-01-01 00:00:00.0",  # 阶梯开始日期
    }
}

NULL_LADDER_RESPONSE = {
    "sta": "00",
    "data": {
        "result": [],
        "totalPower": None,
        "totalElectricity": None,
        # 阶梯数据为 null 的情况
        "ladderEle": None,
        "ladderEleTariff": None,
        "ladderEleSurplus": None,
        "ladderEleStartDate": None,
    }
}

def parse_ladder_data(resp_data):
    """解析阶梯数据"""
    print("=== 阶梯数据解析 ===\n")

    # 检查 ladderEle
    ladder_ele = resp_data.get("ladderEle")
    print(f"ladderEle (阶梯档位): {ladder_ele}")
    if ladder_ele is not None:
        ladder_int = int(ladder_ele)
        ladder_names = {
            0: "电能替代",
            1: "居民阶梯一",
            2: "居民阶梯二",
            3: "居民阶梯三",
        }
        print(f"  -> 解析为整数: {ladder_int}")
        print(f"  -> 阶梯名称: {ladder_names.get(ladder_int, '未知')}")
    else:
        print(f"  -> ⚠️ ladderEle 为 null，无法获取阶梯信息！")

    # 检查 ladderEleTariff
    tariff = resp_data.get("ladderEleTariff")
    print(f"\nladderEleTariff (当前电价): {tariff}")
    if tariff is not None:
        print(f"  -> 解析为浮点数: {float(tariff)} 元/千瓦时")
    else:
        print(f"  -> ⚠️ ladderEleTariff 为 null，无法获取电价！")

    # 检查 ladderEleSurplus
    surplus = resp_data.get("ladderEleSurplus")
    print(f"\nladderEleSurplus (剩余电量): {surplus}")
    if surplus is not None:
        print(f"  -> 解析为浮点数: {float(surplus)} kWh")
    else:
        print(f"  -> ⚠️ ladderEleSurplus 为 null，无法获取剩余电量！")

    # 检查 ladderEleStartDate
    start_date = resp_data.get("ladderEleStartDate")
    print(f"\nladderEleStartDate (阶梯开始日期): {start_date}")
    if start_date is not None:
        try:
            dt = datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S.%f")
            print(f"  -> 解析为日期时间: {dt}")
        except Exception as e:
            print(f"  -> ⚠️ 日期解析失败: {e}")
    else:
        print(f"  -> ⚠️ ladderEleStartDate 为 null！")

    print("\n=== 可能导致阶梯数据为 null 的原因 ===")
    print("1. 月初数据尚未更新（通常1-3号数据不完整）")
    print("2. API 接口返回格式发生变化")
    print("3. 电表或计费系统数据同步延迟")
    print("4. 账号绑定的计量点信息不正确")

if __name__ == "__main__":
    print("测试正常响应:")
    parse_ladder_data(EXAMPLE_API_RESPONSE["data"])

    print("\n" + "="*50 + "\n")

    print("测试 null 响应:")
    parse_ladder_data(NULL_LADDER_RESPONSE["data"])
