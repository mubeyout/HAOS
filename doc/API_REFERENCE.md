# 昆仑燃气 API 数据字段参考

本文档详细说明从昆仑燃气API返回的数据字段，方便调试和扩展功能。

---

## API 端点汇总

| 端点 | 认证 | 功能 | 状态 |
|-------|--------|------|------|
| `/api/v1/open/recharge/getUserDebtByUserCode` | ❌ | 查询余额和基本信息 | ✅ 可用 |
| `/api/v1/close/recharge/getPaymentRecordList` | ✅ | 查询缴费记录 | ✅ 可用 |
| `/api/v1/close/recharge/getMonthlyTotalGasVolume` | ✅ | 查询月度用气量和阶梯价格 | ✅ 可用 |
| `/api/v1/close/recharge/smartMeterGasDaysRecords/{mdmCode}/{userCode}` | ✅ | 查询每日读数 | ✅ 可用 |
| `/api/v1/close/user/getUserCode` | ✅ | 查询客户详细信息 | ✅ 可用 |

---

## API 端点: getUserDebtByUserCode

**请求参数**:
```json
{
  "cid": 2,
  "userCode": "xxxxxxxx",
  "terminalType": 7
}
```

---

## 响应数据结构

### 成功响应示例

```json
{
  "success": true,
  "data": {
    "accountId": "123456789",
    "userCode": "xxxxxxxx",
    "customerName": "张*三",
    "address": "云南省昆明市**区***路***号***",
    "remoteMeterBalance": 100.50,
    "meterType": "IC卡燃气表",
    "mdmCode": "MDM001",
    "readingLastTime": "2026-02-13 14:30:00",
    "remoteMeterLastCommunicationTime": "2026-02-13 14:25:00",
    "oweAmount": 0,
    "lastPaymentAmount": 100.00,
    "lastPaymentTime": "2026-01-15 10:20:00",
    "ladderStage": 1,
    "ladderPrice": {
      "ladder1": {"price": 2.97, "start": 0, "end": 360},
      "ladder2": {"price": 3.56, "start": 360, "end": 540},
      "ladder3": {"price": 4.46, "start": 540, "end": 9999}
    },
    "currentLadder": {
      "stage": 1,
      "unitPrice": 2.97
    }
  }
}
```

---

## 数据字段说明

### 账户信息

| 字段名 | 类型 | 说明 | 示例值 |
|--------|------|------|--------|
| `accountId` | String | 账户唯一标识 | "123456789" |
| `userCode` | String | 户号 | "xxxxxxxx" |
| `customerName` | String | 客户姓名（脱敏） | "张*三" |
| `address` | String | 安装地址（脱敏） | "云南省昆明市**区***" |

### 余额信息

| 字段名 | 类型 | 说明 | 示例值 |
|--------|------|------|--------|
| `remoteMeterBalance` | Float | 表端余额（元） | 100.50 |
| `oweAmount` | Float | 欠费金额（元） | 0 |

### 表计信息

| 字段名 | 类型 | 说明 | 示例值 |
|--------|------|------|--------|
| `meterType` | String | 表计类型 | "IC卡燃气表" |
| `mdmCode` | String | MDM设备代码 | "MDM001" |
| `readingLastTime` | String | 最近读表时间 | "2026-02-13 14:30:00" |
| `remoteMeterLastCommunicationTime` | String | 最近通讯时间 | "2026-02-13 14:25:00" |

### 缴费信息

| 字段名 | 类型 | 说明 | 示例值 |
|--------|------|------|--------|
| `lastPaymentAmount` | Float | 上次缴费金额 | 100.00 |
| `lastPaymentTime` | String | 上次缴费时间 | "2026-01-15 10:20:00" |

### 阶梯价格信息

| 字段名 | 类型 | 说明 | 示例值 |
|--------|------|------|--------|
| `ladderStage` | Integer | 当前阶梯（1/2/3） | 1 |
| `ladderPrice.ladder1.price` | Float | 第一阶梯单价 | 2.97 |
| `ladderPrice.ladder1.start` | Integer | 第一阶梯起始用量（m³） | 0 |
| `ladderPrice.ladder1.end` | Integer | 第一阶梯结束用量（m³） | 360 |
| `ladderPrice.ladder2.price` | Float | 第二阶梯单价 | 3.56 |
| `ladderPrice.ladder2.start` | Integer | 第二阶梯起始用量 | 360 |
| `ladderPrice.ladder2.end` | Integer | 第二阶梯结束用量 | 540 |
| `ladderPrice.ladder3.price` | Float | 第三阶梯单价 | 4.46 |
| `ladderPrice.ladder3.start` | Integer | 第三阶梯起始用量 | 540 |
| `ladderPrice.ladder3.end` | Integer | 第三阶梯结束用量 | 9999 |
| `currentLadder.stage` | Integer | 当前所属阶梯 | 1 |
| `currentLadder.unitPrice` | Float | 当前单价 | 2.97 |

---

## API 端点: smartMeterGasDaysRecords

**完整URL**: `https://bol.grs.petrochina.com.cn/api/v1/close/recharge/smartMeterGasDaysRecords?days=30`

**请求参数**:
```json
{
  "cid": 2,
  "userCode": "xxxxxxxx",
  "terminalType": 7
}
```

### 响应数据结构

```json
{
  "success": true,
  "data": {
    "smartMeterGasDaysRecords": [
      {
        "readingLastTime": "2026-02-13 14:30:00",
        "remoteMeterBalance": 100.00,
        "gasVolume": 0.52,
        "gasFee": 1.53
      },
      {
        "readingLastTime": "2026-02-12 15:20:00",
        "remoteMeterBalance": 100.50,
        "gasVolume": 0.48,
        "gasFee": 1.42
      }
    ]
  }
}
```

### 用气量字段说明

| 字段名 | 类型 | 说明 | 示例值 |
|--------|------|------|--------|
| `readingLastTime` | String | 读表时间 | "2026-02-13 14:30:00" |
| `remoteMeterBalance` | Float | 该时间点余额 | 100.00 |
| `gasVolume` | Float | 用气量（m³） | 0.52 |
| `gasFee` | Float | 气费（元） | 1.53 |

---

## API 端点: getPaymentRecordList (缴费记录)

**完整URL**: `https://bol.grs.petrochina.com.cn/api/v1/close/recharge/getPaymentRecordList`

**认证**: 需要登录（Cookie）

**请求参数**:
```json
{
  "cid": 2,
  "pageNumber": 1,
  "pageSize": 10,
  "userCodeId": "用户的userCodeId"
}
```

### 响应示例

```json
{
  "code": 1,
  "data": {
    "customerName": "张三",
    "recordsCount": "15",
    "recordsInfoList": [
      {
        "operationDate": "2026-01-02",
        "operationTime": "17:23:00",
        "payAmount": "50.0",
        "payOrgDesc": "昆明公司APP",
        "paySourceDesc": "移动APP",
        "payStatusDesc": "完成",
        "payItemType": "第三方代收实时"
      }
    ]
  },
  "success": true
}
```

### 缴费记录字段说明

| 字段名 | 类型 | 说明 | 示例值 |
|--------|------|------|--------|
| `operationDate` | String | 操作日期 | "2026-01-02" |
| `operationTime` | String | 操作时间 | "17:23:00" |
| `payAmount` | Float | 缴费金额 | "50.0" |
| `payOrgDesc` | String | 缴费机构 | "昆明公司APP" |
| `paySourceDesc` | String | 支付来源 | "移动APP" |
| `payStatusDesc` | String | 支付状态 | "完成" |
| `payItemType` | String | 支付项目类型 | "第三方代收实时" |

---

## API 端点: getMonthlyTotalGasVolume (月度用量+阶梯价格)

**完整URL**: `https://bol.grs.petrochina.com.cn/api/v1/close/recharge/getMonthlyTotalGasVolume`

**认证**: 需要登录（Cookie）

**请求参数**:
```json
{
  "userCode": "xxxxxxxx",
  "cid": 2,
  "page": 1,
  "pageSize": 7
}
```

**注意**: 响应内容经过 **Base64 编码**，需要先解码再解析 JSON。

### 响应示例

```json
{
  "code": 1,
  "data": {
    "address": "云南省昆明市**区***",
    "badgeNumber": "1422112233115116",
    "customerName": "张三",
    "rateItemInfo": [
      {
        "beginVolume": "0.0",
        "endVolume": "360",
        "price": "2.97",
        "rateName": "第一阶梯"
      },
      {
        "beginVolume": "360",
        "endVolume": "540",
        "price": "3.56",
        "rateName": "第二阶梯"
      },
      {
        "beginVolume": "540",
        "endVolume": "9999999",
        "price": "4.46",
        "rateName": "第三阶梯"
      }
    ],
    "recordsInfo": [
      {
        "gasFee": "236.4",
        "gasVolume": "11.8",
        "gasYear": "2025年08月"
      }
    ],
    "totalGasVolume": "26.35"
  },
  "success": true
}
```

### 月度用量字段说明

| 字段名 | 类型 | 说明 | 示例值 |
|--------|------|------|--------|
| `rateItemInfo` | Array | 阶梯价格配置（3个阶梯） | - |
| `recordsInfo` | Array | 月度用量记录 | - |
| `totalGasVolume` | Float | 总用气量 | "26.35" |
| `gasYear` | String | 年月 | "2025年08月" |
| `gasVolume` | Float | 月用气量（m³） | "11.8" |
| `gasFee` | Float | 月费用（元） | "236.4" |

### 阶梯价格配置

根据 API 返回的 `rateItemInfo`：

| 阶梯 | 起始用量 | 结束用量 | 单价 |
|-------|----------|----------|------|
| 第一阶梯 | 0 m³ | 360 m³ | 2.97 元/m³ |
| 第二阶梯 | 360 m³ | 540 m³ | 3.56 元/m³ |
| 第三阶梯 | 540 m³ | 无限制 | 4.46 元/m³ |

---

## 错误响应

### 认证失败

```json
{
  "success": false,
  "code": "401",
  "message": "用户认证失败"
}
```

### 账户不存在

```json
{
  "success": false,
  "code": "404",
  "message": "账户不存在"
}
```

### 请求超时

```json
{
  "success": false,
  "code": "504",
  "message": "请求超时，请稍后重试"
}
```

---

## 数据计算公式

### 日用气量计算
```
今日用气量 = smartMeterGasDaysRecords[0].gasVolume
今日费用 = smartMeterGasDaysRecords[0].gasFee
```

### 月用气量计算
```
月用气量 = SUM(smartMeterGasDaysRecords[n].gasVolume) for n in 本月
月费用 = SUM(smartMeterGasDaysRecords[n].gasFee) for n in 本月
```

### 年用气量计算
```
年用气量 = SUM(月用气量)
年费用 = SUM(月费用)
```

### 当前阶梯判断
```
IF 年累计用量 <= 360: 阶梯1
ELIF 年累计用量 <= 540: 阶梯2
ELSE: 阶梯3
```

---

## HTTP Headers 请求头

```http
POST /api/v1/open/recharge/getUserDebtByUserCode HTTP/1.1
Host: bol.grs.petrochina.com.cn
User-Agent: Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.47(0x18002f2f) NetType/WIFI Language/zh_CN
Content-Type: application/json;charset=UTF-8
```

---

## 调试建议

1. **使用 Proxyman 或 Charles 抓包**
   - 安装SSL证书
   - 配置代理
   - 运行微信小程序
   - 导出HAR文件分析

2. **使用 curl 测试**
   ```bash
   curl -X POST \
     'https://bol.grs.petrochina.com.cn/api/v1/open/recharge/getUserDebtByUserCode' \
     -H 'Content-Type: application/json;charset=UTF-8' \
     -H 'User-Agent: Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) ...' \
     -d '{"cid":2,"userCode":"xxxxxxxx","terminalType":7}'
   ```

3. **Home Assistant 日志查看**
   - 设置 → 系统 → 日志
   - 搜索 `petrochina_gas`
   - 查看API请求和响应

---

*创建日期: 2026-02-13*
*版本: 1.0*
