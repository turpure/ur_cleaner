#! usr/bin/env/python3
# coding:utf-8
# Author: turpure

import os
import datetime
from src.services.base_service import CommonService
import requests
from multiprocessing.pool import ThreadPool as Pool
import math


class Worker(CommonService):
    """
    get joom refund
    """

    def __init__(self):
        super().__init__()
        self.base_name = 'mssql'
        self.cur = self.base_dao.get_cur(self.base_name)
        self.con = self.base_dao.get_connection(self.base_name)
        self.col = self.get_mongo_collection('joom', 'joom_refund')
      

    def close(self):
        self.base_dao.close_cur(self.cur)

    def get_joom_token(self):
        sql = 'select AccessToken, aliasName from S_JoomSyncInfo'
        self.cur.execute(sql)
        ret = self.cur.fetchall()
        for row in ret:
            yield row

    def get_order(self, token_info):
        token = token_info['AccessToken']
        url = 'https://api-merchant.joom.com/api/v2/order/multi-get'
        headers = {'content-type': 'application/json', 'Authorization': 'Bearer ' + token}

        date = str(datetime.datetime.today() - datetime.timedelta(days=3))[:10]
        # yesterday = str(datetime.datetime.today() - datetime.timedelta(days=1))[:10]
        # date = str(datetime.datetime.strptime(yesterday[:8] + '01', '%Y-%m-%d'))[:10]
        limit = 300
        start = 0
        try:
            while True:
                param = {
                    "since": date,
                    "limit": limit,
                    'start': start
                }
                ret = None
                for i in range(2):
                    try:
                        response = requests.get(url, params=param, headers=headers)
                        ret = response.json()
                        break
                    except Exception as why:
                        self.logger.info(f' fail to get page of {token_info["aliasName"]} {i + 1} times cause of {why}')

                if ret and ret['code'] == 0 and ret['data']:
                    self.parse(ret['data'])
                    start += limit
                    if len(ret['data']) < limit:
                        break
                else:
                    break

        except Exception as e:
            self.logger.error(e)

    def parse(self, rows):
        for order in rows:
            try:
                order_detail = order["Order"]
                if order_detail['state'] == 'REFUNDED':
                    ele = {'order_id': order_detail['order_id'], 'refund_time': order_detail['refunded_time'],
                                  'total_value': order_detail['order_cost'], 'currencyCode': 'USD', 'plat': 'joom'}
                    self.put(ele)
            except Exception as why:
              self.logger.error(f'fail to parse rows cause of {why}')

    def clean(self):
        self.col.delete_many({})
        self.logger.info('success to clear joom_refund')

    def put(self, row):
        # self.col.save(row)
        self.col.insert_one(row)

    def pull(self):
        rows = self.col.find()
        for row in rows:
            yield (row['order_id'], row['refund_time'], row['total_value'], row['currencyCode'], row['plat'])

    def push_batch(self, rows):
        try:
            rows = list(rows)
            number = len(rows)
            step = 100
            end = math.ceil(number / step)
            for i in range(0, end):
                value = ','.join(map(str, rows[i * step: min((i + 1) * step, number)]))
                sql = f'insert into y_refunded(order_id, refund_time, total_value,currencyCode, plat) values {value}'
                try:
                    self.cur.execute(sql)
                    self.con.commit()
                    self.logger.info(f"success to save data of joom refund from {i * step} to  {min((i + 1) * step, number)}")
                except Exception as why:
                    self.logger.error(f"fail to save data of joom refund cause of {why} ")
        except Exception as why:
            self.logger.error(f"fail to save joom refund cause of {why} ")

    def push_one(self, rows):
        try:

            sql = ("if not EXISTS (select id from y_refunded(nolock) where "
                       "order_id=%s and refund_time= %s) "
                       'insert into y_refunded(order_id, refund_time, total_value,currencyCode, plat) '
                       'values(%s,%s,%s,%s,%s)')
            for row in rows:
                self.cur.execute(sql, (row[0], row[1], row[0], row[1], row[2], row[3], row[4]))
            self.con.commit()
        except Exception as why:
            self.logger.error(f"fail to save joom refund cause of {why} ")

    def save_trans(self):
        rows = self.pull()
        self.push_one(rows)

    def work(self):
        try:
            tokens = self.get_joom_token()
            self.clean()
            pl = Pool(2)
            pl.map(self.get_order, tokens)
            pl.close()
            pl.join()
            self.save_trans()
        except Exception as why:
            self.logger.error('fail to count sku cause of {} '.format(why))
            name = os.path.basename(__file__).split(".")[0]
            raise Exception(f'fail to finish task of {name}')
        finally:
            self.close()
            mongo.close()


if __name__ == "__main__":
    import time
    start = time.time()
    worker = Worker()
    worker.work()
    end = time.time()
    date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(end))
    print(date + f' it takes {end - start} seconds')



