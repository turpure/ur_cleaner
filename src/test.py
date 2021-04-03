#! usr/bin/env/python3
# coding:utf-8
# @Time: 2018-10-20 15:56
# Author: turpure

from src.services.base_service import CommonService
from ebaysdk.trading import Connection as Trading
import datetime
from pymongo import MongoClient
from configs.config import Config


# class AliSync(BaseService):
class AliSync(CommonService):
    """
    check purchased orders
    """

    def __init__(self):
        super().__init__()
        self.config = Config().get_config('ebay.yaml')
        self.mongodb = self.mongo['operation']
        self.col = self.get_mongo_collection('operation', 'wish_stock_task')
        # self.base_name = 'mysql'
        # self.cur = self.base_dao.get_cur(self.base_name)
        # self.con = self.base_dao.get_connection(self.base_name)

    # def close(self):
    #     self.base_dao.close_cur(self.cur)

    def get_ebay_description(self):
        try:
            token = "AgAAAA**AQAAAA**aAAAAA**4cDcXQ**nY+sHZ2PrBmdj6wVnY+sEZ2PrA2dj6ADmYCiCJCKowydj6x9nY+seQ**kykBAA**AAMAAA**2raaq3ZjHDQ4DiKqgsIU8yUrmXhnO/E+Tr2d4L3iuN1gisy+zj98RKBw428kEtvZWwsStHqLx4la1EY3Dj0ZQnjr43xCp8Jnc8VCUDV5N4eN+E+LF6Rb6VxGVp8hKUAfugt7QnudjbDauQjCCUA9SDoYJzQ9u/rwRJ5QVEZucKSnvTdifZ8c0jChwZ/ef/qe3aUTpEObghcU597C/G47rfSp6bHH+hDaEyRVdfENahD/ysQRjZN4CG8C/XRSsgphCv0OqKx+/wK//68Yy7/fnG0vxJ75kceLFkFFSfILRB4afumjfHR9WG7yvgqXfAmkB0oppaSFWPZMv/mjRTfPaCjyP+ZeT6H+hKWTmnBnzJEcvdM3As8rcTgpEr9AXoGowK4I7LAle8WuIqLzCpvqpldIl4BUcrmipX2tngP/XBSE0UieQthBh3RUgBmAazaoZ+bVMMT9GKy8DpzZ/WbcirwI7YNCZNWMRIjJWCUJ8mv15baOXwvN3u9GtWqZRhi+m+xCHCQ45CbHTw1Y56Y8sJuZRnwmB8kpshRNXRBX6VZjeEW2prBnpIbmhHBeOubbPdB3EwEu6FKziSXgyK5tkdM/LDOnj6WRQGSHcNBhvt0pFFLrYOmoTqLgWRs9lC27ByG4IebXMWf1iTM3qvppvpEsPTzoBZywHT2tftQd/6iAi1O+ZcFMsziV+tpIy++KteSwyJuQY0hEV885RDDYplsgwbLnB+oBbL44p6iWgjckjLgjiqwOC8XrMiBWjC2S"
            api = Trading(config_file=self.config)
            trade_response = api.execute(
                'GetItem',
                {
                    'ItemID': 293716165258,
                #     'SKU': row['Item']['SKU'],
                #     # 'SKU': '7C2796@#01',
                    'requesterCredentials': {'eBayAuthToken': token},
                }
            )
            ret = trade_response.dict()
            print(ret)
            if ret['Ack'] == 'Success':
                return ret
            else:
                return []
        except Exception as e:
            self.logger.error(f"error cause of {e}")

    def run(self):
        try:
            # for i in range(33):
            #     begin = str(datetime.datetime.strptime('2020-08-01', '%Y-%m-%d') + datetime.timedelta(days=i))[:10]
            #     # print(begin)
            #     rows = self.get_data(begin)
            #     for row in rows:
            #         # print(row)
            #         col2.update_one({'recordId': row['recordId']}, {"$set": row}, upsert=True)
            #     self.logger.info(f'success to sync data in {begin}')
            #res = self.get_ebay_description()
            item = {
                'item_id': '6062bc31893e9afe58745377',
            'suffix': 'WISE180-neatthao',
            'sku': '6A557301',
            'goodsCode': '6A5573',
            'goodsStatus': '在售',
            'mainImage': 'https://canary.contestimg.wish.com/api/webimage/6062bc31893e9afe58745377-original.jpg?cache_buster=-5461400121706197611',
            'shopSku': '6A557301@#E180',
            'onlineInventory': 0,
            'targetInventory': 10000,
            'goodsName': '保鲜袋收纳袋',
            'status': '待执行',
            'executedResult': '',
            'executedTime': '',
            'created': '2021-04-02 13:55:00',
            'updated': '2021-04-02 13:55:00',
            'accessToken': '111'
            }
            self.col.insert_one(item)
            # update_time = str(datetime.datetime.today())[:19]
            # print(update_time)


            # for item in res['DescriptionTemplate']:
            #     self.col.insert_one(item)
            # for item in res['ThemeGroup']:
            #     self.col1.insert_one(item)
        except Exception as e:
            self.logger(e)
        # finally:
        #     self.close()


if __name__ == '__main__':
    sync = AliSync()
    sync.run()
