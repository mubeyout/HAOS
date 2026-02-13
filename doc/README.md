# 昆仑燃气 Home Assistant 集成

## 项目概述

为昆仑燃气用户提供数据统计和监控功能，基于微信小程序API开发。

---

## 📋 功能清单

### ✅ 已实现功能

1. **账户管理**
   - 支持多个燃气账户
   - 配置户号、地区代码(CID)、终端类型
   - 每小时自动更新一次数据

2. **微信授权登录（可选）**
   - 支持微信授权码登录
   - 获取完整数据（缴费记录、用量统计、阶梯价格）
   - 也可跳过登录，仅查看基础余额信息

3. **余额查询**
   - 实时显示燃气表余额
   - 单位：人民币(CNY)

4. **客户信息**
   - 用户名
   - 详细地址
   - 所属燃气公司
   - 账户ID

5. **表计监控**
   - 最近表读数
   - 最后通讯时间
   - 表计类型

6. **缴费记录**（需要登录）
   - 上次缴费金额
   - 上次缴费时间
   - 待上表金额

7. **用气统计**（需要登录）
   - 今日用气量/费用
   - 上月用气量/费用
   - 今年累计用气量/费用
   - 近10天/30天用量统计

8. **阶梯价格**（需要登录）
   - 当前所属阶梯
   - 各阶梯价格范围
   - 第一阶梯：2.97元/m³ (0-360m³)
   - 第二阶梯：3.56元/m³ (360-540m³)
   - 第三阶梯：4.46元/m³ (540m³以上)

---

## 🔧 配置参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|---------|------|
| `user_code` | string | 必填 | 燃气户号(8位数字) |
| `cid` | number | 2 | 地区代码（见下方说明） |
| `terminal_type` | number | 7 | 终端类型（一般保持默认） |
| `wechat_code` | string | 可选 | 微信授权码（用于获取完整数据） |

### 地区代码 (CID) 说明

**CID 是区分不同燃气分公司的关键参数：**

| 地区 | CID |
|------|-----|
| 昆明分公司 | 2 |
| 其他地区 | 请联系当地燃气公司确认 |

**如果查询失败：**
1. 确认您的燃气所属分公司
2. 尝试不同的 CID 值
3. 联系当地燃气公司确认正确的地区代码

---

## 🚀 快速开始

### 步骤 1：安装集成

```bash
# 复制项目到HACS自定义集成目录
cp -r HAOS/petrochina-gas ~/homeassistant/.homeassistant/custom_components/petrochina_gas

# 重启Home Assistant
# 或在配置 → 集成与服务 → 添加集成 → 搜索 "昆仑燃气"
```

### 步骤 2：配置集成

1. 打开Home Assistant
2. 进入 设置 → 集成与服务
3. 点击 "添加集成" → 搜索 "昆仑燃气"
4. 按照三步流程配置：

#### 第一步：微信授权（可选）
- 输入微信授权码（从昆仑燃气小程序获取）
- 或勾选「跳过登录」仅查看基础信息

#### 第二步：账户信息
- **户号**: 8位数字（如 15068622）
- **地区代码**: 2（昆明分公司）
- **终端类型**: 7（默认值）

#### 第三步：确认配置
- 检查配置信息
- 点击提交完成配置

### 步骤 3：验证传感器

配置完成后，您会看到以下传感器（以户号15068622为例）：

| 传感器 | 说明 | 需要登录 |
|--------|------|----------|
| `sensor.petrochina_gas_15068622_balance` | 当前余额(元) | ❌ |
| `sensor.petrochina_gas_15068622_gas_company` | 燃气公司 | ❌ |
| `sensor.petrochina_gas_15068622_user_code` | 户号 | ❌ |
| `sensor.petrochina_gas_15068622_customer_name` | 用户名 | ❌ |
| `sensor.petrochina_gas_15068622_address` | 地址 | ❌ |
| `sensor.petrochina_gas_15068622_meter_reading` | 最近表读数 | ❌ |
| `sensor.petrochina_gas_15068622_last_communication` | 最后通讯时间 | ❌ |
| `sensor.petrochina_gas_15068622_owe_amount` | 待上表金额 | ✅ |
| `sensor.petrochina_gas_15068622_last_payment` | 上次缴费 | ✅ |
| `sensor.petrochina_gas_15068622_daily_volume` | 今日用气量 | ✅ |
| `sensor.petrochina_gas_15068622_daily_cost` | 今日费用 | ✅ |
| `sensor.petrochina_gas_15068622_monthly_volume` | 上月用气量 | ✅ |
| `sensor.petrochina_gas_15068622_monthly_cost` | 上月费用 | ✅ |
| `sensor.petrochina_gas_15068622_yearly_volume` | 今年累计用气量 | ✅ |
| `sensor.petrochina_gas_15068622_yearly_cost` | 今年累计费用 | ✅ |
| `sensor.petrochina_gas_15068622_recent_usage` | 近10/30天用量 | ✅ |
| `sensor.petrochina_gas_15068622_ladder_stage` | 当前阶梯 | ✅ |
| `sensor.petrochina_gas_15068622_ladder_price` | 阶梯价格详情 | ✅ |
| `sensor.petrochina_gas_15068622_current_ladder` | 当前阶梯与单价 | ✅ |

---

## 📦 文件结构

```
petrochina-gas/
├── __init__.py           # 集成入口
├── const.py              # 常量定义
├── config_flow.py        # 配置流程
├── sensor.py             # 传感器实体
├── manifest.json         # 集成清单
├── strings.json         # 多语言字符串
├── services.yaml        # 服务定义
└── gas_client/         # API客户端包
    ├── __init__.py      # 包导出
    ├── const.py         # API常量
    ├── client.py        # HTTP客户端
    └── models.py       # 数据模型
```

---

## 🔍 API信息

### 基础URL
```
https://bol.grs.petrochina.com.cn
```

### 主要API端点

| API | 用途 | 认证 |
|-----|------|------|
| `/api/v1/open/weixin/userAuthorization` | 微信授权登录 | ❌ |
| `/api/v1/open/recharge/getUserDebtByUserCode` | 查询余额 | ❌ |
| `/api/v1/close/recharge/getPaymentRecordList` | 缴费记录 | ✅ |
| `/api/v1/close/recharge/getMonthlyTotalGasVolume` | 月度用量+阶梯价格 | ✅ |
| `/api/v1/close/recharge/smartMeterGasDaysRecords/{mdmCode}/{userCode}` | 每日用量 | ✅ |

---

## ⚠️ 注意事项

1. **地区代码(CID)**:
   - 不同分公司有不同的CID
   - 昆明分公司使用 `2`
   - 如果查询失败，请确认正确的CID

2. **微信授权**:
   - 授权码有时效性，过期需重新获取
   - 跳过登录只能查看基础信息

3. **数据更新**:
   - 传感器每小时自动更新一次
   - 可手动触发刷新

---

## 🤚 自动化示例

### 余额低提醒

```yaml
automation:
  - alias: "燃气余额低提醒"
    trigger:
      - platform: numeric_state
        entity_id: sensor.petrochina_gas_15068622_balance
        below: 50
    action:
      - service: notify.mobile_app
        data:
          message: "燃气余额不足50元，请及时充值！"
```

### 月度用气报告

```yaml
automation:
  - alias: "月度用气报告"
    trigger:
      - platform: time
        at: "20:00:00"
    condition:
      - condition: template
        value_template: "{{ now().day == 1 }}"
    action:
      - service: notify.mobile_app
        data:
          message: >
            上月用气量: {{ states('sensor.petrochina_gas_15068622_monthly_volume') }} m³
            上月费用: {{ states('sensor.petrochina_gas_15068622_monthly_cost') }} 元
            当前阶梯: {{ states('sensor.petrochina_gas_15068622_current_ladder') }}
```

---

## 🐛 问题排查

### Q: 配置后没有显示传感器？

**解决方法:**
1. 检查配置文件是否正确填写
2. 查看Home Assistant日志 (设置 → 系统 → 日志)
3. 确认集成已正确安装
4. 重启Home Assistant

### Q: 传感器显示unavailable？

**解决方法:**
1. 检查户号是否正确（8位数字）
2. 检查地区代码是否正确
3. 检查网络连接
4. 查看日志中的错误信息
5. 尝试不同的CID值

### Q: 部分传感器无数据？

**可能原因:**
- 这些传感器需要微信登录
- 请在配置时输入有效的微信授权码
- 或重新配置集成，添加授权码

---

## 📊 当前状态

- ✅ 基础架构已完成
- ✅ 微信登录已实现
- ✅ 18个传感器已实现
- ✅ 配置流程已完成
- ✅ Token管理已实现
- ⏳ 待实际测试验证

---

*创建日期: 2026-02-13*
*最后更新: 基于微信小程序API*
