#!/usr/bin/env python3
"""
地区代码诊断脚本
用于检查南网账户的地区代码配置
"""

import json

# 地区代码映射
AREACODE_MAPPING = {
    # Yunnan Province (05)
    "050000": "云南省",
    "050100": "昆明市",
    "050200": "曲靖市",
    "050300": "玉溪市",
    # ... 其他城市

    # Guangdong Province (03)
    "030000": "广东省",
    "030100": "广州市",
    "030300": "深圳市",
    # ... 其他城市
}

def analyze_area_code(area_code: str):
    """分析地区代码"""
    province_code = area_code[:2] + "0000"
    province = AREACODE_MAPPING.get(province_code, "未知省份")
    city = AREACODE_MAPPING.get(area_code, "未知城市")

    return province, city

def main():
    print("=== 南网地区代码诊断 ===\n")

    # 从错误日志中提取的信息
    print("错误日志分析:")
    print("  地区代码: 050100")
    print("  用户编号: 0501133211814158")
    print("  计量点号: 2111111127130798")
    print()

    province, city = analyze_area_code("050100")
    print(f"代码解析 050100:")
    print(f"  省份: {province}")
    print(f"  城市: {city}")
    print()

    print("但错误消息显示: '深圳电费日历查询返回'")
    print("这说明可能存在以下问题:")
    print("  1. 账户配置的地区代码不正确")
    print("  2. 服务器端地区代码映射不一致")
    print("  3. 账户属于深圳但在昆明使用")
    print()

    print("=== 解决方案 ===")
    print()
    print("方案 1: 检查账户配置")
    print("  在 Home Assistant 中检查集成配置，确认账户信息中的 area_code")
    print()
    print("方案 2: 重新绑定账户")
    print("  在南网在线 https://95598.csg.cn 检查账户绑定是否正确")
    print()
    print("方案 3: 手动测试 API")
    print("  运行 csg_client_demo.py 查看返回的地区代码")
    print()

    print("=== 常见地区代码 ===")
    common_codes = [
        ("030100", "广州市"),
        ("030300", "深圳市"),
        ("050100", "昆明市"),
        ("040100", "南宁市"),
        ("060100", "贵阳市"),
        ("070100", "海口市"),
    ]
    for code, name in common_codes:
        print(f"  {code} = {name}")

if __name__ == "__main__":
    main()
