# 极客科技订单工单系统 API 规范 v1.0

## 1. 概述
本文档定义极客科技内部订单查询与工单创建的标准接口，供客服系统、ERP 等调用。

## 2. 接口域名
- 生产环境：`https://api.geektech.com/v1`
- 测试环境：`http://localhost:8000`

## 3. 订单查询接口

### 3.1 请求方式
`GET /order/{order_id}`

### 3.2 路径参数
| 参数名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| order_id | string | 是 | 订单号，格式如 `ORD-20260411-1234` |

### 3.3 返回示例
```json
{
  "status": "success",
  "order_id": "ORD-20260411-1234",
  "order_status": "已发货",
  "logistics": "中通快递 ZT123456789",
  "items": "极客智能音箱 x1"
}