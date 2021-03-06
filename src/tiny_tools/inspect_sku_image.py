#! usr/bin/env/python3
# coding:utf-8
# @Time: 2019-08-28 15:45
# Author: turpure


import asyncio

import aiohttp

from pymongo import MongoClient

MONGO_HOST = '127.0.0.1'
MONGO_PORT = 27017
MONGO_DB = 'crawlab_test'

mongo = MongoClient(host=MONGO_HOST, port=MONGO_PORT)
db = mongo[MONGO_DB]
col = db['sku_image']


async def process_response(resp, **kwargs):
    image = kwargs.get('image')
    status = resp.status  # 读取状态
    col.update({'image': image}, {'$set': {'http_status': status}})


async def request_site(image: str, semaphore):
    _image = image
    async with semaphore:
        async with aiohttp.ClientSession() as session:  # <1> 开启一个会话
            async with session.get(_image) as resp:  # 发送请求
                await process_response(resp=resp, image=image)
                print('crawled ' + _image)


async def run():
    try:
        semaphore = asyncio.Semaphore()  # 限制并发量为100
        images = [site['image'] for site in col.find({'http_status': {'$eq': 0}})]
        to_get = [request_site(image, semaphore) for image in images]
        await asyncio.wait(to_get)
    except Exception as e:
        print('failed to get image cause of {}'.format(e))


if __name__ == '__main__':
    import time
    start = time.time()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
    loop.close()
    mongo.close()
    print('it takes {} seconds'.format(time.time() - start))
