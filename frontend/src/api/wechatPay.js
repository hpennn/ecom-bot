/**
 * 微信支付 API
 */
import request from '@/utils/request'

/**
 * 获取微信支付配置
 */
export function getWechatPayConfig() {
  return request({
    url: '/api/wechat-pay/config',
    method: 'get'
  })
}

/**
 * 创建微信支付订单
 * @param {Object} data - 订单数据
 * @param {string} data.description - 商品描述
 * @param {number} data.amount - 支付金额（分）
 * @param {string} data.pay_type - 支付类型: native/jsapi
 * @param {string} [data.openid] - 用户openid（JSAPI支付必填）
 * @param {string} [data.attach] - 附加数据
 * @param {string} [data.order_id] - 自定义订单号
 */
export function createWechatOrder(data) {
  return request({
    url: '/api/wechat-pay/create-order',
    method: 'post',
    data
  })
}

/**
 * 查询订单状态
 * @param {string} orderId - 订单号
 */
export function queryWechatOrder(orderId) {
  return request({
    url: `/api/wechat-pay/query-order/${orderId}`,
    method: 'get'
  })
}

/**
 * 获取支付二维码
 * @param {string} orderId - 订单号
 */
export function getPayQrcode(orderId) {
  return `${import.meta.env.VITE_API_BASE_URL || ''}/api/wechat-pay/qrcode/${orderId}`
}

/**
 * 关闭订单
 * @param {string} orderId - 订单号
 */
export function closeWechatOrder(orderId) {
  return request({
    url: `/api/wechat-pay/close-order/${orderId}`,
    method: 'post'
  })
}
