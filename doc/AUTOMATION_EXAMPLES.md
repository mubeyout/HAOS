# 昆仑燃气 Home Assistant 自动化示例

本文档提供常用的自动化场景示例，帮助你更好地监控和管理燃气账户。

---

## 1. 余额低提醒

当燃气余额低于设定阈值时发送通知。

```yaml
alias: "燃气余额低提醒"
description: "当燃气余额低于30元时发送通知"
trigger:
  - platform: numeric_state
    entity_id: sensor.petrochina_gas_xxxxxxxx_balance
    below: 30
condition: []
action:
  - service: notify.mobile_app_your_phone
    data:
      title: "⚠️ 燃气余额不足"
      message: "当前燃气余额为 {{ states('sensor.petrochina_gas_xxxxxxxx_balance') }} 元，请及时充值！"
      data:
        push:
          sound: default
          badge: 5
mode: single
```

---

## 2. 每日用气量统计

每天晚上记录当日用气量到统计传感器。

```yaml
alias: "每日燃气用量记录"
description: "每天晚上10点记录当日用气量"
trigger:
  - platform: time
    at: "22:00:00"
condition: []
action:
  - service: utility_meter.update
    target:
      entity_id: utility_meter.daily_gas_consumption
    data:
      value: "{{ states('sensor.petrochina_gas_xxxxxxxx_daily_volume') }}"
mode: single
```

---

## 3. 月度用量报告

每月初发送上月用气量报告。

```yaml
alias: "月度燃气用量报告"
description: "每月1日上午9点发送上月用量报告"
trigger:
  - platform: time
    at: "09:00:00"
condition:
  - condition: template
    value_template: "{{ now().day == 1 }}"
action:
  - service: notify.mobile_app_your_phone
    data:
      title: "📊 上月燃气用量报告"
      message: |
        上月用气量: {{ states('sensor.petrochina_gas_xxxxxxxx_monthly_volume') }} m³
        上月用气费用: {{ states('sensor.petrochina_gas_xxxxxxxx_monthly_cost') }} 元
        当前余额: {{ states('sensor.petrochina_gas_xxxxxxxx_balance') }} 元
mode: single
```

---

## 4. 阶梯价格变化提醒

当阶梯价格发生变化时发送通知。

```yaml
alias: "燃气阶梯价格变化提醒"
description: "当当前阶梯发生变化时发送通知"
trigger:
  - platform: state
    entity_id: sensor.petrochina_gas_xxxxxxxx_ladder_stage
condition:
  - condition: template
    value_template: "{{ trigger.from_state.state != trigger.to_state.state }}"
action:
  - service: notify.mobile_app_your_phone
    data:
      title: "📈 燃气阶梯变化"
      message: |
        燃气阶梯已从 {{ trigger.from_state.state }} 变更为 {{ trigger.to_state.state }}
        当前单价: {{ state_attr('sensor.petrochina_gas_xxxxxxxx_current_ladder', 'unit_price') }} 元/m³
mode: single
```

---

## 5. 表计通讯异常提醒

当表计通讯时间超过24小时时发送警告。

```yaml
alias: "燃气表通讯异常提醒"
description: "当表计超过24小时未通讯时发送警告"
trigger:
  - platform: template
    value_template: >
      {{ (as_timestamp(now()) - as_timestamp(states.sensor.petrochina_gas_xxxxxxxx_last_communication.last_updated)) > 86400 }}
condition:
  - condition: state
    entity_id: sensor.petrochina_gas_xxxxxxxx_last_communication
    state: "unknown"
action:
  - service: notify.mobile_app_your_phone
    data:
      title: "⚠️ 燃气表通讯异常"
      message: "燃气表已超过24小时未通讯，请检查设备状态！"
mode: single
```

---

## 6. 缴费记录自动化

记录每次缴费到历史数据库（需要配置 recorder 或 history）。

```yaml
alias: "燃气缴费记录"
description: "记录缴费信息到辅助传感器"
trigger:
  - platform: state
    entity_id: sensor.petrochina_gas_xxxxxxxx_last_payment
condition:
  - condition: template
    value_template: "{{ trigger.from_state.state != trigger.to_state.state }}"
action:
  - service: logbook.log
    data:
      name: 燃气缴费
      message: "缴费金额: {{ state_attr('sensor.petrochina_gas_xxxxxxxx_last_payment', 'amount') }} 元，时间: {{ state_attr('sensor.petrochina_gas_xxxxxxxx_last_payment', 'time') }}"
      entity_id: sensor.petrochina_gas_xxxxxxxx_last_payment
mode: single
```

---

## 7. Dashboard 传感器卡片示例

在 Lovelace Dashboard 中添加燃气信息卡片。

```yaml
type: entities
title: 昆仑燃气监控
entities:
  - entity: sensor.petrochina_gas_xxxxxxxx_balance
    name: 余额
    icon: mdi:currency-cny
  - entity: sensor.petrochina_gas_xxxxxxxx_daily_volume
    name: 今日用气量
    icon: mdi:fire
  - entity: sensor.petrochina_gas_xxxxxxxx_daily_cost
    name: 今日费用
    icon: mdi:cash
  - entity: sensor.petrochina_gas_xxxxxxxx_meter_reading
    name: 表计读数
    icon: mdi:gauge
  - entity: sensor.petrochina_gas_xxxxxxxx_last_communication
    name: 最后通讯
    icon: mdi:clock-outline
  - entity: sensor.petrochina_gas_xxxxxxxx_ladder_stage
    name: 当前阶梯
    icon: mdi:stairs
state_color: true
```

---

## 8. 图表卡片配置

使用 `apexcharts-card` 或 `history-graph` 显示用量趋势。

### 使用 history-graph（内置）:

```yaml
type: history-graph
entities:
  - entity: sensor.petrochina_gas_xxxxxxxx_daily_volume
    name: 每日用气量
hours_to_show: 168  # 显示7天
refresh_interval: 3600
```

### 使用 apexcharts-card（需要 HACS 安装）:

```yaml
type: custom:apexcharts-card
graph_span: 7d
header:
  title: 每日燃气用量趋势
  show: true
  show_states: true
series:
  - entity: sensor.petrochina_gas_xxxxxxxx_daily_volume
    name: 用气量 (m³)
    type: column
    stroke_width: 2
```

---

## 9. 智能家居联动

根据用气量自动调整其他设备。

```yaml
alias: "高用气量时调整新风系统"
description: "当检测到用气量高时（可能在使用燃气灶），开启新风系统"
trigger:
  - platform: numeric_state
    entity_id: sensor.petrochina_gas_xxxxxxxx_daily_volume
    above: 0.5  # m³
    for:
      minutes: 5
condition:
  - condition: state
    entity_id: input_boolean.gas_cooking_detected
    state: "on"
action:
  - service: fan.turn_on
    target:
      entity_id: fan.fresh_air_system
    data:
      percentage: 50
mode: single
```

---

## 10. 多账户聚合视图

如果有多个燃气账户，创建聚合视图。

```yaml
type: custom:group-card
title: 燃气账户汇总
entities:
  - type: custom:bar-card
    entities:
      - entity: sensor.petrochina_gas_xxxxxxxx_balance
        min: 0
        max: 500
        name: 账户1
      - entity: sensor.petrochina_gas_yyyyyyyy_balance
        min: 0
        max: 500
        name: 账户2
    direction: right
    height: 40px
```

---

## 💡 使用说明

1. **修改实体ID**: 将示例中的 `xxxxxxxx` 替换为你的实际户号（8位数字）
2. **修改通知服务**: 将 `mobile_app_your_phone` 替换为你的 Home Assistant 通知服务
3. **调整阈值**: 根据实际需要调整余额阈值、用气量阈值等
4. **安装依赖**: 某些卡片（如 apexcharts-card）需要通过 HACS 安装

---

## 📦 推荐的 HACS 插件

以下插件可以增强燃气监控体验：

- **apexcharts-card**: 高级图表显示
- **card-mod**: 自定义卡片样式
- **button-card**: 创建自定义按钮
- **lovelace-card-mod**: 卡片样式修改

---

*创建日期: 2026-02-13*
*适用于: petrochina_gas 集成*
