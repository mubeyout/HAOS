#!/usr/bin/env python3
"""分析HAR文件中的登录认证流程"""

import json
import sys

def main():
    # 读取 HAR 文件（请修改为实际路径）
    har_file_path = '/path/to/your/file.har'
    try:
        with open(har_file_path, 'r', encoding='utf-8') as f:
        har = json.load(f)

    entries = har.get('log', {}).get('entries', [])

    print('=' * 70)
    print(' 登录认证流程分析 '.center(60))
    print('=' * 70)

    # 1. 查找登录请求
    print('\n【1. 登录请求】\n')
    for entry in entries:
        url = entry.get('request', {}).get('url', '')
        if 'userAuthorization' in url:
            method = entry.get('request', {}).get('method', '')
            print(f'方法: {method}')
            print(f'URL: {url}')

            # 请求头
            headers = entry.get('request', {}).get('headers', [])
            print('\n关键请求头:')
            for h in headers:
                name = h.get('name', '')
                if 'cookie' in name.lower() or 'token' in name.lower():
                    val = h.get('value', '')
                    print(f'  {name}: {val[:80]}...' if len(val) > 80 else f'  {name}: {val}')

            # 请求体
            post_data = entry.get('request', {}).get('postData', {})
            if post_data:
                print('\n请求体:')
                try:
                    if isinstance(post_data, str):
                        data = json.loads(post_data)
                    else:
                        data = post_data
                    params = data.get('params', [])
                    if params:
                        param_json = json.loads(params[0].get('name', '{}'))
                        print(json.dumps(param_json, indent=2, ensure_ascii=False))
                except Exception as e:
                    print(f'解析错误: {e}')

            # 响应
            response = entry.get('response', {})
            status = response.get('status', 0)
            content = response.get('content', {})
            response_text = content.get('text', '')

            print(f'\n响应状态: {status}')

            if response_text:
                print('\n响应内容:')
                try:
                    data = json.loads(response_text)
                    print(json.dumps(data, indent=2, ensure_ascii=False))
                except:
                    print(response_text[:500])
            break

    # 2. 查找登录后的第一个需要认证的请求
    print('\n' + '=' * 70)
    print('【2. 登录后的认证使用】\n')

    found_close_api = False
    for entry in entries:
        url = entry.get('request', {}).get('url', '')
        if '/api/v1/close/' in url and not found_close_api:
            found_close_api = True

            # 提取API名称
            api_name = url.split('/')[-1]
            print(f'API: {api_name}')
            print(f'完整URL: {url}')

            # 获取请求头中的Cookie
            headers = entry.get('request', {}).get('headers', [])
            cookie_value = None
            for h in headers:
                if h.get('name', '').lower() == 'cookie':
                    cookie_value = h.get('value', '')
                    print('\nCookie (前200字符):')
                    print(f'  {cookie_value[:200]}...')
                    break

            # 请求体
            post_data = entry.get('request', {}).get('postData', {})
            if post_data:
                print('\n请求体:')
                try:
                    if isinstance(post_data, str):
                        data = json.loads(post_data)
                    else:
                        data = post_data
                    print(json.dumps(data, ensure_ascii=False)[:300])
                except:
                    print(post_data[:300])

            # 响应
            response = entry.get('response', {})
            status = response.get('status', 0)
            print(f'\n响应状态: {status}')

            # 检查是否成功
            content = response.get('content', {})
            response_text = content.get('text', '')
            if response_text and len(response_text) < 500:
                try:
                    data = json.loads(response_text)
                    if data.get('success') or data.get('successWithData'):
                        print('结果: 成功')
                    else:
                        print(f'结果: 失败 - {data.get("message", "未知错误")}')
                except:
                    pass

            print('-' * 70)
            break

    if not found_close_api:
        print('未找到需要认证的 close API 请求')

    print('\n' + '=' * 70)
    print('【3. 总结】')
    print('=' * 70)
    print("""
认证方式: Cookie-based

关键Cookie字段:
- Hm_lvt_xxx (百度统计，非必须)
- Hm_lpvt_xxx (百度统计，非必须)

登录API: /api/v1/open/wechat/userAuthorization
参数:
  - cid: 地区代码 (99999表示全国)
  - code: 微信授权码
  - unionId: 微信OpenID

注意: 这是一个"开放"API，不需要Cookie即可登录
登录后调用"close"API时，会自动携带Cookie
    """)

if __name__ == '__main__':
    main()
