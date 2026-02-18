# HAOS 能源集成

> 为 Home Assistant 提供中国本地化的能源数据监控功能

[![Home Assistant](https://img.shields.io/badge/Home_Assistant-2024.11+-blue.svg)](https://www.home-assistant.io/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

本目录包含三个用于（云南）能源服务的 Home Assistant 集成插件。

## 📦 目录

- [概述](#概述)
- [快速开始](#快速开始)
- [南网电网集成 (HA-grid-south-master)](#南网电网集成)
- [昆明水务集成 (kunming_water)](#昆明水务集成)
- [中石油燃气集成 (petrochina_gas)](#中石油燃气集成)
- [常见问题](#常见问题)
- [免责声明](#免责声明)
- [打赏与支持](#打赏与支持)

---

## 📖 概述

这三个集成插件为 Home Assistant 提供了中国本地化的能源数据监控功能：

| 集成名称 | 功能描述 | 传感器数量 | 更新频率 |
|---------|---------|-----------|---------|
| **南网电网** | 中国南方电网用电数据查询，支持阶梯电价 | 19个 | 默认4小时 |
| **昆明水务** | 昆明市自来水用水数据查询，支持阶梯水价 | 6个 | 默认1小时 |
| **中石油燃气** | 中石油燃气用气数据查询，支持阶梯气价 | 22个 | 默认1小时 |

---

## 🚀 快速开始

### 通用安装步骤

所有三个集成的安装方法相同：

```bash
# 1. 将对应目录复制到 Home Assistant 的 custom_components 目录
cp -r <集成目录> /path/to/homeassistant/custom_components/<集成名称>

# 2. 重启 Home Assistant

# 3. 在 Home Assistant 中添加集成
# 设置 → 设备与服务 → 添加集成 → 搜索对应名称
```

### 集成名称对照

| 集成 | 目录名 | custom_components 名称 | 搜索关键词 |
|------|--------|----------------------|-----------|
| 南网电网 | `HA-grid-south-master` | `china_southern_power_grid_stat` | China Southern Power Grid |
| 昆明水务 | `kunming_water` | `kunming_water` | Kunming Water |
| 中石油燃气 | `petrochina_gas` | `petrochina_gas` | PetroChina Gas |

---

## ⚡ 南网电网集成

### 功能介绍

中国南方电网用电数据监控集成，支持广东、广西、云南、贵州、海南五省区用户查询用电信息。

> **鸣谢**: 本集成基于 [china_southern_power_grid_stat](https://github.com/CubicPill/china_southern_power_grid_stat) 项目开发，在此基础上了补齐了阶梯电价和自动计算功能。

**主要功能：**
- 实时查询账户余额和欠费情况
- 查看每日、每月、每年用电量和电费
- 自动识别当前阶梯电价档位
- 显示年度阶梯累计用电量和剩余电量
- 支持多账户管理

### 安装方法

参见 [快速开始](#快速开始) 部分的通用安装步骤。

简要步骤：
1. 复制 `HA-grid-south-master` 目录到 `custom_components/china_southern_power_grid_stat`
2. 重启 Home Assistant
3. 添加集成，搜索 "China Southern Power Grid Statistics"

### 配置步骤

#### 登录方式（三选一）

**方式一：手机号+验证码登录**
```
1. 输入手机号（南网在线注册手机号）
2. 点击发送验证码
3. 输入收到的验证码完成登录
```

**方式二：南网APP扫码登录**
```
1. 打开"南网在线"APP
2. 扫描Home Assistant显示的二维码
3. 在手机上确认登录
```

**方式三：微信/支付宝扫码登录**
```
1. 使用微信或支付宝扫描二维码
2. 在手机上确认登录授权
```

#### 添加电费账户

登录成功后：
1. 系统自动获取已绑定的电费账户列表
2. 选择要添加的账户（可添加多个）
3. 设置数据更新间隔（默认4小时）

### 传感器列表及中文对照

| 传感器ID | 中文名称 | 单位 | 说明 |
|---------|---------|------|------|
| `balance` | 账户余额 | CNY | 当前账户可用余额 |
| `arrears` | 欠费金额 | CNY | 当前欠费金额 |
| `yesterday_kwh` | 昨日用电量 | kWh | 前一天的总用电量 |
| `latest_day_kwh` | 最近一日用电量 | kWh | 最新有数据的日期用电量 |
| `latest_day_cost` | 最近一日电费 | CNY | 最新日期用电费用 |
| `this_month_total_usage` | 本月用电量 | kWh | 当月累计用电量 |
| `this_month_total_cost` | 本月电费 | CNY | 当月累计电费 |
| `this_year_bill_usage` | 本年账单用量 | kWh | 已结算月份账单用量之和 |
| `this_year_bill_cost` | 本年账单费用 | CNY | 已结算月份账单费用之和 |
| `this_year_total_usage` | 本年实际用电量 | kWh | 账单用量+本月用量 |
| `this_year_total_cost` | 本年实际电费 | CNY | 账单费用+本月费用 |
| `last_month_total_usage` | 上月用电量 | kWh | 上个月用电量 |
| `last_month_total_cost` | 上月电费 | CNY | 上个月电费 |
| `last_year_total_usage` | 去年用电量 | kWh | 去年全年用电量 |
| `last_year_total_cost` | 去年电费 | CNY | 去年全年电费 |
| `current_ladder` | 当前阶梯 | - | 当前阶梯档位(1-4) |
| `current_ladder_tariff` | 当前阶梯电价 | CNY/kWh | 当前阶梯单价 |
| `current_ladder_remaining_kwh` | 当前阶梯剩余电量 | kWh | 距离下一阶梯的剩余电量 |
| `yearly_ladder_total_kwh` | 年度阶梯累计用电 | kWh | 本年度累计用电量 |

#### 阶梯电价说明（以云南为例）

| 阶梯 | 名称 | 用电范围 | 单价 |
|-----|------|---------|------|
| 1 | 电能替代 | 0-1560 kWh/年 | 0.3595 元/度 |
| 2 | 居民阶梯一 | 1561-3600 kWh/年 | 0.4495 元/度 |
| 3 | 居民阶梯二 | 3601-4680 kWh/年 | 0.4995 元/度 |
| 4 | 居民阶梯三 | 4681 kWh以上/年 | 0.7995 元/度 |

*注：不同地区阶梯档位和价格可能有所不同*

### 实体ID命名规则

```
sensor.china_southern_power_grid_stat_{户号}_{传感器后缀}
```

例如：`sensor.china_southern_power_grid_stat_0501133211814158_balance`

---

## 💧 昆明水务集成

### 功能介绍

昆明自来水公司用水数据监控集成，支持昆明市区用户查询用水信息。

**主要功能：**
- 查询账户余额
- 查看每日、每月用水量
- 自动识别当前阶梯水价档位
- 显示最新抄表数据

### 安装方法

参见 [快速开始](#快速开始) 部分的通用安装步骤。

简要步骤：
1. 复制 `kunming_water` 目录到 `custom_components/kunming_water`
2. 重启 Home Assistant
3. 添加集成，搜索 "Kunming Water"

### 配置步骤

#### 前置准备

在配置前，需要先完成注册和户号绑定：

1. 访问 [昆明水务服务平台](https://km96106.cn/browserClient/index/index.action)
2. 注册账号并绑定你的户号

#### 登录配置

在 Home Assistant 中添加集成后，使用手机号+验证码登录：

1. 输入户号
2. 输入注册时绑定的手机号
3. 点击"发送验证码"
4. 输入收到的验证码完成登录配置

### 传感器列表及中文对照

| 传感器ID | 中文名称 | 单位 | 说明 |
|---------|---------|------|------|
| `balance` | 账户余额 | CNY | 水费账户可用余额 |
| `last_payment` | 最近缴费 | CNY | 最近一次缴费金额 |
| `monthly_usage` | 本月用水量 | m³ | 当月累计用水量 |
| `daily_usage` | 每日用水量 | m³ | 最新日用水量 |
| `unit_price` | 当前水价 | CNY/m³ | 当前阶梯水价单价 |
| `ladder_stage` | 当前阶梯 | - | 当前阶梯档位(1-3) |

#### 阶梯水价说明（昆明市民用）

| 阶梯 | 用水范围 | 单价 |
|-----|---------|------|
| 1 | 0-12.5 m³/月 | 4.20 元/m³ |
| 2 | 12.5-17.5 m³/月 | 5.80 元/m³ |
| 3 | 17.5 m³以上/月 | 10.60 元/m³ |

### 实体ID命名规则

```
sensor.kunming_water_{用户编号}_{传感器后缀}
```

---

## 🔥 中石油燃气集成

### 功能介绍

中石油燃气用气数据监控集成，支持使用中石油燃气服务的用户查询用气信息。

**主要功能：**
- 查询账户余额和欠费
- 查看每日、每月、每年用气量
- 自动识别当前阶梯气价档位
- 显示最近缴费记录
- 显示智能表具通信状态

### 安装方法

参见 [快速开始](#快速开始) 部分的通用安装步骤。

简要步骤：
1. 复制 `petrochina_gas` 目录到 `custom_components/petrochina_gas`
2. 重启 Home Assistant
3. 添加集成，搜索 "PetroChina Gas"

### 配置步骤

#### 前置准备

在配置前，需要先完成注册和户号绑定：

**方式一：网页注册（推荐）**
1. 访问 [中石油燃气服务平台](https://bol.grs.petrochina.com.cn/)
2. 注册账号并绑定你的户号
3. 记录你的 **户号 (userid)** 和 **地区代码 (cid)**

**方式二：小程序绑定**
> 若网页中没有你所在的地区，可通过"昆仑慧享+"小程序进行绑定

#### 获取地区代码 (cid)

昆明地区 cid 为 `2`，其他地区可通过以下方式获取：

- **参考论坛**: [HASS论坛教程](https://bbs.hassbian.com/thread-24800-1-1.html)
- **抓包获取**: 使用 Proxyman 等工具抓取微信小程序 "昆仑慧享+" 的网络请求，分析获取对应地区的 cid；若不会的本人提供有偿服务或指导（50元一次）

#### 登录配置

在 Home Assistant 中添加集成后，使用密码登录：

| 配置项 | 说明 | 示例 |
|-------|------|------|
| `userid` | 你的户号 | 0501133211814158 |
| `cid` | 地区和燃气公司代码 | 昆明为 2 |
| 手机号 | 注册时绑定的手机号 | 138xxxx xxxx |
| 密码 | 登录密码 | ******** |
### 传感器列表及中文对照

| 传感器ID | 中文名称 | 单位 | 说明 |
|---------|---------|------|------|
| `balance` | 账户余额 | CNY | 燃气账户可用余额 |
| `arrears` | 欠费金额 | CNY | 当前欠费金额 |
| `owe_amount` | 欠费总额 | CNY | 包含滞纳金的欠费总额 |
| `customer_name` | 客户姓名 | - | 账户注册姓名 |
| `address` | 用气地址 | - | 燃气使用地址 |
| `current_month_volume` | 本月用气量 | m³ | 当月累计用气量 |
| `current_month_cost` | 本月燃气费 | CNY | 当月累计燃气费用 |
| `monthly_volume` | 月度用气量 | m³ | 最新账单月用气量 |
| `monthly_cost` | 月度燃气费 | CNY | 最新账单月燃气费用 |
| `yearly_volume` | 年度用气量 | m³ | 本年累计用气量 |
| `yearly_cost` | 年度燃气费 | CNY | 本年累计燃气费用 |
| `last_day_usage` | 最近日用气量 | m³ | 最新日期用气量 |
| `last_day_usage_cost` | 最近日燃气费 | CNY | 最新日期燃气费用 |
| `last_day_usage_time` | 最近用气日期 | - | 最新用气数据日期 |
| `recent_monthly_usage` | 近31天用量 | m³ | 最近31天累计用气 |
| `recent_monthly_cost` | 近31天费用 | CNY | 最近31天累计费用 |
| `meter_reading` | 表具读数 | m³ | 智能表最新读数 |
| `last_communication` | 表具最后通信时间 | - | 表具最后上报数据时间 |
| `ladder_stage` | 当前阶梯 | - | 当前阶梯档位 |
| `ladder_price` | 当前气价 | CNY/m³ | 当前阶梯单价 |
| `ladder_remaining` | 阶梯剩余量 | m³ | 距离下一阶梯剩余量 |
| `last_payment` | 最近缴费金额 | CNY | 最近一次缴费金额 |
| `last_payment_date` | 最近缴费日期 | - | 最近一次缴费时间 |

### 实体ID命名规则

```
sensor.petrochina_gas_{用户编号}_{传感器后缀}
```

---

## ❓ 常见问题

### Q1: 为什么传感器显示 "unavailable"？

**A:** 可能的原因：
1. 登录token已过期 → 尝试重新配置集成
2. 网络连接问题 → 检查Home Assistant网络连接
3. API服务器维护 → 等待一段时间后重试
4. 更新间隔太长 → 在设置中调整更新频率

### Q2: 本月电费/燃气费如何计算？

**A:** 由于账单通常在下月出具，本月费用采用自动计算：
```
本月费用 = 本月用量 × 当前阶梯单价
```
例如：本月用电100 kWh，当前阶梯电价0.3595元/度
```
本月电费 = 100 × 0.3595 = 35.95 元
```

### Q3: 阶梯档位每年/每月如何重置？

**A:**
- **电费**：年度阶梯，每年1月1日重置
- **水费**：月度阶梯，每月1日重置
- **燃气费**：年度阶梯，每年1月1日重置

### Q4: 如何查看更详细的用电/用水/用气明细？

**A:** 部分集成提供属性数据：
1. 在Home Assistant中点击传感器实体
2. 查看属性（Attributes）部分
3. 包含每日明细、月度汇总等详细信息

### Q5: 支持哪些地区？

**A:**
- **南网电网**：广东、广西、云南、贵州、海南五省区
- **昆明水务**：昆明市及下辖区域
- **中石油燃气**：使用中石油燃气的各地区（具体服务范围咨询当地燃气公司）

### Q6: 如何添加多个账户？

**A:** 在集成设置中：
1. 进入已添加集成的设置页面
2. 选择"添加条目"
3. 使用同一登录方式登录
4. 选择要添加的新账户

### Q7: 更新频率可以调整吗？

**A:** 可以，在集成设置中：
- **南网电网**：默认4小时，可调整为1-24小时
- **昆明水务**：默认1小时，可调整为30分钟-12小时
- **中石油燃气**：默认1小时，可调整为30分钟-12小时

*注意：过于频繁的更新可能增加API服务器负担*

### Q8: 数据准确性如何保证？

**A:**
- 所有数据直接来自官方API
- 数据更新与官方系统同步
- 如有差异，以官方APP/网站数据为准

---

## ⚠️ 免责声明

本集成插件仅供个人学习和研究使用，使用本插件所产生的任何后果由使用者自行承担。

- 插件通过官方API获取数据，不对数据的准确性和实时性做任何保证
- 请遵守相关服务提供商的使用条款
- 如有疑问，请以官方APP/网站数据为准

---

## 💬 打赏与支持

如果你觉得这些集成对你有帮助，欢迎打赏支持：

<img width="auto" height="400px" alt="微信图片_20260218063244_75_4" src="https://github.com/user-attachments/assets/0c26d24d-800c-4558-bb76-0fc06c3812c6" />
<img width="auto" height="400px" alt="微信图片_20260218063244_75_4" src="https://github.com/user-attachments/assets/01183a44-c8f7-4bc0-8920-4fd850fb7d0b" />

技术交流或寻求有偿服务（QQ群）
<img width="938" height="1100" alt="image" src="https://github.com/user-attachments/assets/9f9a2073-ff99-405d-8fa3-dac15b39589b" />



