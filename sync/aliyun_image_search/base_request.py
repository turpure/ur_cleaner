#! usr/bin/env/python3
# coding:utf-8
# @Time: 2019-11-26 11:16
# Author: turpure

from aliyunsdkcore.client import AcsClient
import base64
import aliyunsdkimagesearch.request.v20190325.AddImageRequest as AddImageRequest
import aliyunsdkimagesearch.request.v20190325.DeleteImageRequest as DeleteImageRequest
import aliyunsdkimagesearch.request.v20190325.SearchImageRequest as SearchImageRequest
from configs.config import Config
import requests


class BaseRequest(object):

    def __init__(self):
        config = Config().config
        self.key_id = config['imageSearch']['key_id']
        self.key_secret = config['imageSearch']['key_secret']
        self.region = 'cn-shanghai'
        self.instance = 'yourpicture'
        self.client = AcsClient(self.key_id, self.key_secret, self.region)

    @staticmethod
    def read_image(image_url):
        try:
            res = requests.get(image_url)
            if res.status_code == 200:
                return res.content
        except Exception as why:
            print(f'fail to read image {image_url} cause of {why}')

    def add(self, image_url):

        # 添加图片
        request = AddImageRequest.AddImageRequest()
        request.set_endpoint(f'imagesearch.{self.region}.aliyuncs.com')
        request.set_InstanceName(self.instance)
        request.set_ProductId(image_url)
        request.set_PicName(image_url)
        img = self.read_image(image_url)
        if img:
            encoded_pic_content = base64.b64encode(img)
            request.set_PicContent(encoded_pic_content)
            try:
                response = self.client.do_action_with_exception(request)
                print(response)
                return response
            except Exception as why:
                print(f'fail to add image cause of {why}')
            return None

    def search(self, image_url):
        # 搜索图片
        request = SearchImageRequest.SearchImageRequest()
        request.set_endpoint(f'imagesearch.{self.region}.aliyuncs.com')
        request.set_InstanceName(self.instance)
        img = self.read_image(image_url)
        if img:
            encoded_pic_content = base64.b64encode(img)
            request.set_PicContent(encoded_pic_content)
            try:
                response = self.client.do_action_with_exception(request)
                print(response)
                return response
            except Exception as why:
                print(f'fail to search image cause of {why}')
                return None


if __name__ == '__main__':
    worker = BaseRequest()
    url = 'http://121.196.233.153/images/7A471204.jpg'
    # url = 'http://121.196.233.153/images/Q113701.jpg'
    worker.search(url)