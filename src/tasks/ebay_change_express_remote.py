#! usr/bin/env/python3
# coding:utf-8
# @Time: 2019-02-22 11:30
# Author: turpure

from src.services.base_service import BaseService
from configs.config import Config
from ebaysdk.trading import Connection as Trading
from ebaysdk import exception
import json


class Shipper(BaseService):
    """
    上传跟踪号到eBay后台
    """

    def __init__(self, order_id):
        super().__init__()
        self.config = Config().get_config('ebay.yaml')
        self.order_id = order_id

    def get_orders(self):
        """
        获取订单信息
        :return:
        """
        check_sql = 'select mergeFlag from p_trade(nolock) where nid = %s'
        single_sql = ("select DISTINCT pt.guid as orderId,pt.nid as tradeNid,  pt.trackNo, spi.ebayToken, carrierEN as carrierName, pt.logicswaynid  "
               "from p_trade(nolock) as pt LEFT JOIN S_PalSyncInfo as spi on spi.NoteName = pt.suffix "
               "LEFT JOIN p_tradedt(nolock)  as ptd on pt.nid = ptd.tradeNid "
               "LEFT JOIN B_LogisticWayReg(nolock)  as l on pt.logicswaynid=l.logisticwaynid and l.platform in ('trades','ebay')"
               " where pt.nid = %s")

        merge_sql = (
            "select DISTINCT pb.guid as orderId, pt.nid as tradeNid,  pt.trackNo, spi.ebayToken, carrierEN as carrierName, pt.logicswaynid  "
            "from p_trade(nolock) as pt LEFT JOIN S_PalSyncInfo as spi on spi.NoteName = pt.suffix "
            "LEFT JOIN p_tradedt(nolock)  as ptd on pt.nid = ptd.tradeNid "
            "LEFT JOIN p_trade_b(nolock)  as pb on pt.nid = pb.mergeBillId "
            "LEFT JOIN B_LogisticWayReg(nolock)  as l on pt.logicswaynid=l.logisticwaynid and l.platform in ('trades','ebay')"
            " where pt.nid = %s")
        self.cur.execute(check_sql, (self.order_id,))
        is_merge = self.cur.fetchone()
        if is_merge['mergeFlag'] == 1:
            sql = merge_sql
        else:
            sql = single_sql
        self.cur.execute(sql, (self.order_id,))
        ret = self.cur.fetchall()
        return ret

    def upload_track_number(self, order_info):
        """
        上传订单信息到eBay后台
        :param order_info:
        :return:
        """
        try:
            trade_api = Trading(config_file=self.config)
            params = {
                    # 'TransactionID': order_info['transactionId'],
                    # 'OrderLineItemID': order_info['orderLineItemId'],
                    'OrderID': order_info['orderId'],
                    'Shipped': True,
                    'Shipment': {'ShipmentTrackingDetails':
                                      {
                                          # 'ShipmentLineItem':
                                          #     {'LineItem': {
                                          #         'ItemID': order_info['itemId'], 'TransactionID': order_info['transactionId']}},
                                          'ShippingCarrierUsed': order_info['carrierName'],
                                          'ShipmentTrackingNumber': order_info['trackNo'],
                                       }
                                 },
                    'requesterCredentials': {'eBayAuthToken': order_info['ebayToken']}

                }
            for i in range(2):
                try:
                    resp = trade_api.execute(
                        'CompleteSale', params
                        )
                    ret = resp.dict()
                    if ret["Ack"] == 'Success' or ret["Ack"] == 'Warning':
                        self.logger.info(f'success to upload {order_info["tradeNid"]} with track number {order_info["trackNo"]} ')
                    else:
                        self.logger.info(f'fail to upload {order_info["tradeNid"]} with track number {order_info["trackNo"]} cause of {res} ')
                    break
                except Exception as why:
                    self.logger.info(f'retry {i + 1} times.fail to upload {order_info["tradeNid"]} with track number {order_info["trackNo"]} cause of {why} ')
        except Exception as why:
            self.logger.error(f'fail to upload {order_info["tradeNid"]} with track number {order_info["trackNo"]}'
                              f' cause of {why} ')

    def mark_order_status(self, order_info):
        """
        本地订单标记发货
        :param order_info:
        :return:
        """
        sql = 'update P_trade set shippingmethod=1 where nid=%s'
        try:
            self.cur.execute(sql, (order_info['tradeNid']))
            self.con.commit()
            self.logger.info(f'success to set {order_info["tradeNid"]}  to shipping status ')
        except Exception as e:
            self.logger.info(f'fail to set {order_info["tradeNid"]}  to shipping status ')

    def trans(self, order_info):
        self.upload_track_number(order_info)
        self.mark_order_status(order_info)

    def run(self):
        try:
            orders = self.get_orders()
            for od in orders:
                self.trans(od)

        except Exception as why:
            self.logger.error('fail to  finish task cause of {} '.format(why))
        finally:
            self.close()


if __name__ == "__main__":
    worker = Shipper(21381190)
    worker.run()

