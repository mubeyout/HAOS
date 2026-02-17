#!/usr/bin/env python3
"""
南网阶梯电价诊断脚本
用于检查集成配置和 API 响应状态
"""

import json
import sys
from datetime import datetime

# 检查清单
CHECKLIST = """
=== 阶梯电价传感器诊断检查清单 ===

【1. 检查传感器状态】
在 Home Assistant 中查看以下传感器的状态：
  - sensor.xxxx_current_ladder           (当前阶梯档位)
  - sensor.xxxx_current_ladder_tariff    (当前阶梯电价)
  - sensor.xxxx_current_ladder_remaining_kwh (剩余电量)

预期显示：
  - current_ladder: "电能替代" / "居民阶梯一" / "居民阶梯二" / "居民阶梯三"
  - current_ladder_tariff: 0.3595 / 0.4495 / 0.4995
  - current_ladder_remaining_kwh: 数值 (如 1429.0)

如果显示 "unavailable" 或 "unknown"，继续下面的检查。

【2. 检查日志】
在 Home Assistant 日志中搜索关键词：
  - "ladder"
  - "ladderEle"
  - "queryDayElectricChargeByMPoint"
  - "CSG Account"

查找可能的错误信息：
  - "ladderEle is null"
  - "API error"
  - "timeout"

【3. 常见问题和解决方案】

问题 A: 传感器显示 "unavailable"
原因:
  a) 月初数据尚未更新（每月1-3号数据可能不完整）
  b) API 返回的 ladderEle 字段为 null
  c) 网络超时或 API 错误

解决:
  a) 等待到每月4号后再检查
  b) 检查网页版 https://95598.csg.cn 是否能正常显示阶梯信息
  c) 重新加载集成或重启 Home Assistant

问题 B: 阶梯显示数字而不是名称
原因: 代码版本过旧

解决:
  - 确认使用最新版本的代码
  - 检查 const.py 中是否包含 LADDER_STAGE_NAMES

问题 C: 电价数值不正确
原因: 地区差异或电价政策调整

解决:
  - 对比 https://95598.csg.cn 网页上显示的电价
  - 检查 LADDER_STAGE_INFO 中的电价是否需要更新

【4. 手动检查 API 响应】
可以使用 csg_client_demo.py 来测试：

```bash
cd /path/to/HA-grid-south-master
python3 csg_client_demo.py
```

选择登录方式后，查看输出中的 ladder 信息。

【5. 月份查询范围问题】
注意：api_query_day_electric_charge_by_m_point 查询的是指定月份的数据。

代码注释提到：
  "KNOWN BUG: this api call returns the daily cost data of year_month,
   but the ladder data will be this month's."

这意味着：
  - 当你查询某个月的数据时，返回的日用电数据是那个月的
  - 但 ladder (阶梯) 数据始终是当前月份的

【6. 检查代码中的时间处理】
当前代码使用 (datetime.now().year, datetime.now().month) 查询本月数据。

如果今天是每月1-3号，本月数据可能尚未生成，导致 ladder 信息为 null。

【7. 建议】
如果问题持续存在，可以考虑：
  1. 在月初时使用上月数据来显示阶梯信息
  2. 添加一个配置选项让用户选择显示方式
  3. 在传感器属性中保存最近一次有效的阶梯信息
"""

def main():
    print(CHECKLIST)

    # 当前日期分析
    now = datetime.now()
    print(f"\n=== 当前日期分析 ===")
    print(f"当前日期: {now.strftime('%Y-%m-%d')}")
    print(f"当前月份: {now.month}月")
    print(f"当前日期: {now.day}号")

    if now.day <= 3:
        print(f"\n⚠️ 注意: 当前是月初({now.day}号)，阶梯数据可能尚未更新！")
        print(f"建议等到本月4号后再检查数据。")
    else:
        print(f"\n✓ 数据应该已更新，请检查其他原因。")

    # 模拟数据检查
    print(f"\n=== API 响应字段检查 ===")
    print(f"api_query_day_electric_charge_by_m_point 应返回:")
    print(f"  - ladderEle: 当前阶梯档位 (0, 1, 2, 3)")
    print(f"  - ladderEleTariff: 当前阶梯电价")
    print(f"  - ladderEleSurplus: 当前阶梯剩余电量")
    print(f"  - ladderEleStartDate: 阶梯开始日期")
    print(f"\n如果这些字段为 null，传感器将显示 unavailable")

if __name__ == "__main__":
    main()
