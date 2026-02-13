# 昆仑燃气微信授权码获取指南

## 方法概述

通过微信扫描二维码授权，无需手动抓包获取参数。

---

## 方案：集成内QR登录（推荐）

参考 `HA-grid-south-master` 的实现方式，在Home Assistant配置流程中直接显示二维码。

### 实现步骤

#### 1. 添加QR码生成API接口

在 `gas_client/client.py` 中添加生成二维码的方法：

```python
def api_create_login_qr_code(self) -> tuple[str, str]:
    """
    生成登录二维码

    Returns:
        (login_id, image_link): login_id用于后续查询状态，image_link是二维码图片URL
    """
    url = f"{self._base_url}/api/v1/open/wechat/userAuthorizationQRCode"

    payload = {
        PARAM_CID: self.cid,
    PARAM_TERMINAL_TYPE: self.terminal_type,
    # 添加其他必要参数
    "timestamp": int(time.time() * 1000),
        "nonce": "".join(random.choices("0123456789", k=16))
    }

    response = self._session.post(url, json=payload, timeout=30)
    response.raise_for_status()
    data = response.json()

    if data.get(FIELD_SUCCESS) or data.get(FIELD_SUCCESS_WITH_DATA):
        return data.get("loginId"), data.get("qrCodeUrl")
    else:
        raise CSGAPIError(data.get(FIELD_MESSAGE, "生成二维码失败"))
```

#### 2. 添加QR状态查询API

```python
def api_get_qr_login_status(self, login_id: str) -> tuple[bool, str | None]:
    """
    查询二维码扫描状态

    Args:
        login_id: 二维码登录ID

    Returns:
        (success, auth_token): success是否成功，auth_token是登录后的token
    """
    url = f"{self._base_url}/api/v1/open/wechat/checkQRCodeStatus"

    payload = {
        "loginId": login_id,
        PARAM_CID: self.cid,
    }

    # 轮询检查状态
    response = self._session.post(url, json=payload, timeout=30)
    response.raise_for_status()
    data = response.json()

    if data.get("logged_in"):  # 用户已扫码
        return True, data.get("auth_token")
    else:
        return False, None
```

#### 3. 修改 config_flow.py 实现QR登录步骤

```python
class KunmingGasConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """第一步：选择登录方式"""
        return self.async_show_menu(
            step_id="user",
            menu_options=[
                "qr_login",      # 二维码登录
                "manual_login",  # 手动输入授权码
                "skip_login",    # 跳过登录
            ],
        )

    async def async_step_qr_login(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """二维码登录步骤"""
        client = GasHttpClient(cid=self._cid)

        if user_input is None:
            # 初次显示，生成二维码
            login_id, image_url = await self.hass.async_add_executor_job(
                client.api_create_login_qr_code
            )

            self.context["qr_login_id"] = login_id
            self.context["qr_image_url"] = image_url

            return self.async_show_form(
                step_id="qr_login",
                data_schema=vol.Schema({
                    vol.Required("refresh_qr", default=False): bool
                }),
                description_placeholders={
                    "description": f"<p>请使用微信扫描下方二维码登录昆仑燃气小程序。</p>"
                                    f'<img src="{image_url}" style="width:250px;height:250px;"/>'
                },
            )

        # 用户点击下一步，检查扫码状态
        if user_input.get("refresh_qr"):
            return await self.async_step_qr_login()

        # 检查登录状态
        login_id = self.context["qr_login_id"]
        success, auth_token = await self.hass.async_add_executor_job(
            client.api_get_qr_login_status, login_id
        )

        if success:
            # 登录成功，创建配置
            return await self.async_step_account()
        else:
            # 未扫码，返回重新显示二维码
            return self.async_show_form(
                step_id="qr_login",
                errors={"base": "qr_not_scanned"},
                description_placeholders={
                    "description": f"<p>请使用微信扫描下方二维码。</p>"
                                    f'<img src="{self.context["qr_image_url"]}" style="width:250px;height:250px;"/>'
                },
            )
```

#### 4. 更新 strings.json

```json
{
  "config": {
    "step": {
      "user": {
        "title": "选择登录方式",
        "description": "请选择登录方式",
        "data": {
          "login_method": "登录方式"
        }
      },
      "qr_login": {
        "title": "扫码登录",
        "description": "{instructions}",
        "data": {
          "refresh_qr": "刷新二维码"
        }
      },
      "manual_login": {
        "title": "手动输入",
        "description": "手动输入微信授权码",
        "data": {
          "wechat_code": "微信授权码"
        }
      }
    },
    "error": {
      "qr_not_scanned": "二维码未扫描，请重试"
    }
  }
}
```

---

## 方法：手动获取授权码

如果不想实现QR登录，可以手动获取：

### 步骤1：手机抓包

1. **安装抓包工具**
   - iOS: Stream (推荐)
   - Android: HttpCanary

2. **打开昆仑燃气小程序**
   - 微信 → 搜索"昆仑燃气"

3. **启动抓包并登录**
   - 打开抓包工具
   - 在小程序中点击"我的"或需要登录的功能

4. **查找请求**
   - 找到 `userAuthorization` 相关的请求
   - 查看请求体中的参数

5. **提取参数**
   ```json
   {
     "cid": 2,
     "code": "xxxxxx",      // 微信授权码
     "unionId": "oYyWJ..."  // 微信OpenID
   }
   ```

### 步骤2：使用已有HAR文件

如果您已经抓过包，有HAR文件：

```bash
cd /Volumes/Samsung_T5/Mubey-Work/HAOS/doc
python3 analyze_auth.py
```

在脚本中修改 HAR 文件路径，运行后会显示：
- 登录URL
- 请求参数（code, unionId, cid）
- 响应数据

---

## API端点说明

| 端点 | 说明 | 是否需要登录 |
|------|------|--------------|
| `/api/v1/open/wechat/userAuthorizationQRCode` | 生成登录二维码 | ❌ |
| `/api/v1/open/wechat/checkQRCodeStatus` | 查询扫码状态 | ❌ |
| `/api/v1/open/wechat/userAuthorization` | 授权码登录 | ❌ |
| `/api/v1/open/recharge/getUserDebtByUserCode` | 查询余额 | ❌ |
| `/api/v1/close/recharge/*` | 查询用量/缴费 | ✅ |

---

## 跳过登录说明

如果只想查看余额，可以**跳过登录**：

- 勾选"跳过登录"选项
- 只需输入户号和地区代码
- 功能受限：只能查看余额，无法查看用量统计、阶梯价格等

---

*创建日期: 2026-02-13*
*适用于: petrochina_gas 集成*
