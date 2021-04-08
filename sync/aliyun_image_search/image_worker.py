#! usr/bin/env/python3
# coding:utf-8
# @Time: 2019-11-26 11:08
# Author: turpure


from sync.aliyun_image_search.base_request import BaseRequest
from src.services.base_service import CommonService


class Worker(CommonService):

    def __init__(self):
        super().__init__()
        self.request = BaseRequest()
        self.col = self.get_mongo_collection('product_engine', 'images_tasks')

    def get_images(self):
        images = self.col.find({"doneFlag": 0})
        for row in images:
            yield row

    def mark_image_task(self, image, status):
        try:
            id = image['_id']
            self.col.find_one_and_update({"_id": id}, {"$set": {"doneFlag": status}})
            self.logger.info(f'success to finish task {image["sku"]}')
        except Exception as why:
            self.logger.error(f'fail to save task {image["sku"]} cause of {why}')

    def run(self):
        try:
            images = self.get_images()
            for img in images:
                result = self.request.add(image_url=img['img'], image_name=img['sku'])
                self.mark_image_task(img, status=result)

        except Exception as why:
            self.logger.error(f'fail to run image-worker cause of {why}')
        finally:
            self.mongo.close()
            self.close()


if __name__ == '__main__':
    worker = Worker()
    worker.run()


