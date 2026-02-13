# PetroChina Gas 集成安装指南

## 问题诊断

如果出现 "Invalid handler specified" 错误，是因为 **文件夹名与 domain 不匹配**。

## 解决方案

### 方法 1: 手动安装（推荐）

在 Home Assistant 的 `custom_components` 目录中：

```bash
# 1. 进入 custom_components 目录
cd ~/.homeassistant/custom_components

# 2. 重命名文件夹（关键步骤！）
mv petrochina-gas petrochina_gas

# 3. 重启 Home Assistant
```

### 方法 2: HACS 安装

如果通过 HACS 安装，请确保：
1. 仓库名称与 domain 匹配
2. 下载后在 HA 中重启

## 文件结构验证

正确的文件结构应该是：

```
custom_components/
└── petrochina_gas/          # 注意：下划线，不是连字符
    ├── __init__.py
    ├── manifest.json
    ├── config_flow.py
    ├── const.py
    ├── sensor.py
    ├── strings.json
    ├── requirements.txt
    ├── translations/
    │   ├── en.json
    │   └── zh-Hans.json
    └── gas_client/
        ├── __init__.py
        ├── client.py
        ├── models.py
        └── const.py
```

## manifest.json 配置

```json
{
  "domain": "petrochina_gas",    // 下划线
  "name": "PetroChina Gas Statistics",
  "config_flow": true,
  "icon": "mdi:fire",
  "iot_class": "local_polling",
  ...
}
```

## ConfigFlow 类名

```python
class PetrochinaGasConfigFlow(config_entries.ConfigFlow):
    # domain: petrochina_gas -> PetrochinaGasConfigFlow
```

## 验证步骤

1. 检查文件夹名是否为 `petrochina_gas`（下划线）
2. 检查 manifest.json 中的 domain 是否为 `petrochina_gas`
3. 重启 Home Assistant
4. 清除浏览器缓存
5. 尝试添加集成

## 调试

如果仍然失败，检查 HA 日志：

```
设置 -> 系统 -> 日志
```

搜索 "petrochina" 或 "config_flow" 查看错误信息。
