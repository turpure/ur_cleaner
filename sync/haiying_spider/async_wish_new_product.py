#! usr/bin/env/python3
# coding:utf-8
# @Time: 2019-10-19 14:23
# Author: turpure


import asyncio
import datetime
import json
import math
import copy

import aiohttp
from bson.objectid import ObjectId
from sync.haiying_spider.wish_spider import BaseSpider
from pymongo.errors import DuplicateKeyError


class Worker(BaseSpider):

    def __init__(self, rule_id=None):
        super().__init__()

    async def get_rule(self):
        col = self.mongodb['wish_rule']
        if self.rule_id:
            rule = await col.find_one(ObjectId(self.rule_id))
            rules = [rule]
        else:
            rules = await col.find({'isUsed': 1, 'type': 'auto'}).to_list(length=None)
        return rules

    async def get_product(self, rule):
        url = "http://www.haiyingshuju.com/wish_2.0/product/list"
        async with aiohttp.ClientSession() as session:
            token = await self.log_in(session)
            self.headers['token'] = token
            rule_id = rule['_id']
            rule_type = rule['ruleType']
            del rule['_id']
            time_range = rule['listedTime']
            if time_range :
                listedTime = [self._get_date_some_days_ago(i) for i in time_range]
                rule['genTimeStart'] = listedTime[-1]
                rule['genTimeEnd'] = listedTime[0]
            payload = rule

            response = await session.post(url, data=json.dumps(payload), headers=self.headers)
            ret = await response.json(content_type='application/json')
            total = ret['total']
            total_page = math.ceil(total / 20)
            rows = ret['data']
            await self.save(rows, session, page=1, rule_id=rule_id, rule_type=rule_type)
            if total_page > 1:
                for page in range(2, total_page + 1):
                    payload['index'] = page
                    try:
                        response = await session.post(url, data=json.dumps(payload), headers=self.headers)
                        res = await response.json()
                        await self.save(res['data'], session, page, rule_id, rule_type=rule_type)
                    except Exception as why:
                        self.logger.error(f'error while requesting page {page} cause of {why}')

    async def save(self, rows, session, page, rule_id, rule_type):
        collection = self.mongodb.wish_new_product
        today = str(datetime.datetime.now())
        for row in rows:
            row['ruleType'] = rule_type
            row["rules"] = [rule_id]
            row['recommendDate'] = today
            row['recommendToPersons'] = []
            url = "http://www.haiyingshuju.com/wish_2.0/product/viewNowChart"
            response = await session.post(url, data=json.dumps({'pid': row['pid']}), headers=self.headers)
            row['soldChart'] = await response.json()
            # print(row)
            try:
                await collection.insert_one(row)
                self.logger.debug(f'success to save {row["pid"]}')
            except DuplicateKeyError:
                doc = await  collection.find_one({'pid': row['pid']})
                rules = list(set(doc['rules'] + row['rules']))
                row['rules'] = rules
                del row['_id']
                del row['recommendToPersons']
                await collection.find_one_and_update({'pid': row['pid']}, {"$set": row})
                self.logger.debug(f'update {row["pid"]}')
            except Exception as why:
                self.logger.debug(f'fail to save {row["pid"]} cause of {why}')
        self.logger.info(f'success to save page {page} in async way of rule {rule_id} ')



if __name__ == '__main__':
    import time
    start = time.time()
    worker = Worker()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(worker.run())
    end = time.time()
    print(f'it takes {end - start} seconds')
