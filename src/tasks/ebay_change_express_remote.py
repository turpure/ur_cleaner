#! usr/bin/env/python3
# coding:utf-8
# @Time: 2019-02-22 11:30
# Author: turpure

import os
from src.services.base_service import CommonService
from configs.config import Config
from ebaysdk.trading import Connection as Trading
import datetime
from ebaysdk import exception
import json


class Shipper(CommonService):
    """
    上传跟踪号到eBay后台
    """

    def __init__(self):
        super().__init__()
        self.config = Config().get_config('ebay.yaml')
        self.base_name = 'mssql'
        self.cur = self.base_dao.get_cur(self.base_name)
        self.con = self.base_dao.get_connection(self.base_name)

    def close(self):
        self.base_dao.close_cur(self.cur)

    def get_orders(self, order_id):
        """
        获取订单信息
        :return:
        """
        check_sql = 'select mergeFlag from p_trade(nolock) where nid = %s'
        single_sql = ("select DISTINCT pt.version as orderId,pt.nid as tradeNid,  pt.trackNo, spi.ebayToken, carrierEN as carrierName, pt.logicswaynid  "
               "from p_trade(nolock) as pt LEFT JOIN S_PalSyncInfo as spi on spi.NoteName = pt.suffix "
               "LEFT JOIN p_tradedt(nolock)  as ptd on pt.nid = ptd.tradeNid "
               "LEFT JOIN B_LogisticWayReg(nolock)  as l on pt.logicswaynid=l.logisticwaynid and l.platform in ('trades','ebay')"
               " where pt.nid = %s")

        #  pt.guid as orderId  ==> pt.version as orderId  修改时间 2020-08-15
        merge_sql = (
            "select DISTINCT pb.version as orderId, pt.nid as tradeNid,  pt.trackNo, spi.ebayToken, carrierEN as carrierName, pt.logicswaynid  "
            "from p_trade(nolock) as pt LEFT JOIN S_PalSyncInfo as spi on spi.NoteName = pt.suffix "
            "LEFT JOIN p_tradedt(nolock)  as ptd on pt.nid = ptd.tradeNid "
            "LEFT JOIN p_trade_b(nolock)  as pb on pt.nid = pb.mergeBillId "
            "LEFT JOIN B_LogisticWayReg(nolock)  as l on pt.logicswaynid=l.logisticwaynid and l.platform in ('trades','ebay')"
            " where pt.nid = %s")
        self.cur.execute(check_sql, (order_id,))
        is_merge = self.cur.fetchone()
        if is_merge['mergeFlag'] == 1:
            sql = merge_sql
        else:
            sql = single_sql
        self.cur.execute(sql, (order_id,))
        ret = self.cur.fetchall()
        return ret

    def upload_track_number(self, order_info):
        """
        上传订单信息到eBay后台
        :param order_info:
        :return:
        """
        flag = True
        try:
            trade_api = Trading(config_file=self.config)
            params = {
                    'OrderID': order_info['orderId'],
                    'Shipped': True,
                    'Shipment': {'ShipmentTrackingDetails':
                                      {
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
                        self.logger.info(f'fail to upload {order_info["tradeNid"]} with track number {order_info["trackNo"]}')
                    break
                except Exception as why:
                    self.logger.info(f'retry {i + 1} times.fail to upload {order_info["tradeNid"]} with track number {order_info["trackNo"]} cause of {why} ')
                    flag = False
        except Exception as why:
            self.logger.error(f'fail to upload {order_info["tradeNid"]} with track number {order_info["trackNo"]}'
                              f' cause of {why} ')
            flag = False
        return flag

    def mark_order_status(self, order_info):
        """
        本地订单标记发货
        :param order_info:
        :return:
        """
        sql = 'update P_trade set shippingmethod=1 where nid=%s'
        try:
            self.cur.execute(sql, (order_info['tradeNid']))
            self.logger.info(f'success to set {order_info["tradeNid"]}  to shipping status ')
        except Exception as e:
            self.logger.info(f'fail to set {order_info["tradeNid"]}  to shipping status ')
            raise Exception(f'fail to set {order_info["tradeNid"]}  to shipping status ')

    def set_log(self, order):
        """
        记录操作日志
        :param order:
        :return:
        """
        sql = 'INSERT INTO P_TradeLogs(TradeNID,Operator,Logs) VALUES (%s,%s,%s)'
        try:
            logs = ('ur_cleaner ' + str(datetime.datetime.today())[:19] + ' 标记发货成功 ')
            self.cur.execute(sql, (order['tradeNid'], 'ur_cleaner', logs))
        except Exception as why:
            self.logger.error(f'fail to set log of {order["tradeNid"]}')
            raise Exception(f'fail to set log of {order["tradeNid"]}')

    def ship(self, order_id=''):
        orders = self.get_orders(order_id)
        for od in orders:
            flag = self.upload_track_number(od)
            if flag:
                for i in range(2):
                    try:
                        self.mark_order_status(od)
                        self.set_log(od)
                        self.con.commit()
                        break
                    except Exception as why:
                        self.logger.info(f'trying to commit remote transaction {i + 1} times cause of {why}')
                        self.con.rollback()

    def run(self):
        try:
            self.ship(order_id='22336766')

        except Exception as why:
            self.logger.error('fail to  finish task cause of {} '.format(why))
            name = os.path.basename(__file__).split(".")[0]
            raise Exception(f'fail to finish task of {name}')
        finally:
            self.close()


if __name__ == "__main__":
    worker = Shipper()
    worker.run()


