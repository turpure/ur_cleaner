from abc import abstractmethod
from src.services.base_service import CommonService
from configs.config import Config
import asyncio
import aiohttp
import re


class BaseSpider(CommonService):

    def __init__(self,tupianku_name=1):
        super().__init__()
        config = Config()
        self.tupianku_name = tupianku_name
        self.tupianku_info = config.get_config(f'tupianku{tupianku_name}')
        # self.proxy_url = "http://127.0.0.1:1080"
        self.proxy_url = None
        self.session = aiohttp.ClientSession()
        self.base_name = 'mssql'
        self.cur = self.base_dao.get_cur(self.base_name)
        self.con = self.base_dao.get_connection(self.base_name)

    def close(self):
        self.base_dao.close_cur(self.cur)

    async def login(self):

        base_url = 'https://www.tupianku.com/login'
        form_data = {
            'action':'login',
            'task':'login',
            'return':'',
            'remember':1,
            'username': self.tupianku_info['username'],
            'password': self.tupianku_info['password']
        }
        await self.session.post(base_url, data=form_data, proxy=self.proxy_url)
        self.logger.info(f'success to login tupianku{self.tupianku_name}')

    async def search_image(self, goodsCode):
        base_url = 'https://www.tupianku.com/myfiles'
        form_data = {
            'action':'search',
            'current_folder_id':self.tupianku_info['folder_id'],
            'move_to_folder_id':0,
            'sort':'date_desc',
            'fl_per_page': 800,
            'keyword': goodsCode
        }
        try:
            ret = await self.session.post(base_url, data=form_data, proxy=self.proxy_url,timeout=20)
            ret = self.get_image_ids(await ret.text())
            self.logger.info(f'find {len(ret)} images of {goodsCode}')
            return ret
        except Exception as why:
            # await self.login()
            self.logger.error(f'failed to find images of {goodsCode} cause of {type(why)}')

    async def delete_image(self, goods_code, image_ids=[],):
        base_url = 'https://www.tupianku.com/myfiles'
        form_data = {
            'action': 'delete',
            'current_folder_id': self.tupianku_info['folder_id'],
            'move_to_folder_id': 0,
            'sort': 'date_desc',
            'fl_per_page': 800,
            'keyword': '',
            'file_ids[]': image_ids
        }
        try:
            ret = await self.session.post(base_url, data=form_data, proxy=self.proxy_url, timeout=20)
            self.logger.info(f'success to delete images of {goods_code} ')
            return ret
        except Exception as why:
            # await self.login()
            self.logger.error(f'failed to delete images of {goods_code} cause of {type(why)}')

    @staticmethod
    def get_image_ids(html):
        image_ids = re.findall(r'mf_addfile\((\d+?),', html)
        return image_ids

