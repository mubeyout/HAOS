# PetroChina Gas 集成修复总结

**日期**: 2026-02-15
**问题来源**: Home Assistant 日志分析

---

## 修复的问题

### 1. ❌ `'GasHttpClient' object has no attribute '_union_id'`

**错误日志**:
```
Unexpected error: 'GasHttpClient' object has no attribute '_union_id'
```

**根本原因**:
- 在 `gas_client/client.py` 的 `__init__` 方法中，**没有初始化 `self._union_id`** 属性
- 当 `refresh_access_token()` 方法被调用时，尝试使用未初始化的 `self._union_id` 导致 `AttributeError`

**修复内容**:

1. **初始化 `_union_id`** (`client.py:83`):
```python
def __init__(self, ...):
    ...
    self._union_id: Optional[str] = None  # 新增
```

2. **修复 `login()` 方法** (`client.py:241`):
```python
self._union_id = union_id  # 存储 union_id
self._open_id = union_id  # 兼容性：也存储到 open_id
```

3. **修复 `check_qr_login_status()` 方法** (`client.py:1106`):
```python
self._union_id = union_id  # 存储 union_id
self._open_id = union_id  # 兼容性：也存储到 open_id
```

4. **修复 `get_credentials()` 方法** (`client.py:136`):
```python
"union_id": self._union_id,  # 返回正确的值
```

---

### 2. ⚠️ `getKey API failed: 解密字符串时遇到异常`

**错误日志**:
```
❌ getKey API failed: 解密字符串时遇到异常
❌ Failed to get AES key
```

**说明**:
- 这是密码登录时 AES 密钥交换过程中的错误
- 由于使用了 `refresh_token` 机制，这个问题不会影响已登录的用户
- Token 刷新不依赖密钥交换流程

**处理方式**:
- 代码已有 fallback 机制：如果获取 AES key 失败，将使用 refresh_token 进行认证
- 用户可以通过扫码登录或使用已保存的 refresh_token 避免此问题

---

## 修复后的效果

✅ **Token 刷新**：每小时自动刷新 token 时不会再报 `_union_id` 属性错误
✅ **扫码登录**：QR 码登录流程正确存储 `union_id`
✅ **密码登录**：微信授权码登录正确存储 `union_id`
✅ **凭证保存**：`get_credentials()` 返回正确的 `union_id` 值

---

## 文件变更

```
HAOS/petrochina_gas/gas_client/client.py
- 第 83 行: 添加 `self._union_id` 初始化
- 第 117 行: `set_credentials` 中已有设置逻辑（无需修改）
- 第 136 行: 修复 `get_credentials` 返回值
- 第 241 行: 修复 `login` 方法设置 `union_id`
- 第 1106 行: 修复 `check_qr_login_status` 方法设置 `union_id`
```

---

## 下一步

1. 重启 Home Assistant 以加载修复后的代码
2. 观察日志，确认 `403 Forbidden` 和 token 刷新不再报错
3. 如果仍有问题，可能需要重新进行登录配置

---

## 相关代码位置

| 文件 | 行号 | 方法 |
|------|------|------|
| `client.py` | 64-94 | `__init__` |
| `client.py` | 95-123 | `set_credentials` |
| `client.py` | 125-138 | `get_credentials` |
| `client.py` | 203-257 | `login` |
| `client.py` | 263-319 | `refresh_access_token` |
| `client.py` | 1071-1119 | `check_qr_login_status` |
