#! usr/bin/env/python3
# coding:utf-8
# @Time: 2018-10-30 15:07
# Author: turpure

import datetime
from src.services.base_service import BaseService


class Fetcher(BaseService):
    """
    fetch developer sold detail from erp and put them into data warehouse
    """

    def __init__(self):
        super().__init__()

    def fetch(self, begin_date, end_date, date_flag):
        sql = 'call report_devGoodsProfit (%s, %s, %s)'
        self.warehouse_cur.execute(sql, (begin_date, end_date, date_flag))
        ret = self.warehouse_cur.fetchall()
        for row in ret:
            yield (row['developer'],
                   row['goodsCode'],
                   row['developDate'],
                   row['goodsStatus'],
                   row['sold'] if row['sold'] else 0,
                   row['amt'] if row['amt'] else 0,
                   row['profit'] if row['profit'] else 0,
                   row['rate'],
                   row['ebaySold'] if row['ebaySold'] else 0,
                   row['ebayProfit'] if row['ebayProfit'] else 0,
                   row['wishSold'] if row['wishSold'] else 0,
                   row['wishProfit'] if row['wishProfit'] else 0,
                   row['smtSold'] if row['smtSold'] else 0,
                   row['smtProfit'] if row['smtProfit'] else 0,
                   row['joomSold'] if row['joomSold'] else 0,
                   row['joomProfit'] if row['joomProfit'] else 0,
                   row['amazonSold'] if row['amazonSold'] else 0,
                   row['amazonProfit'] if row['amazonProfit'] else 0,
                   row['dateFlag'],
                   row['orderTime']
                   )

    def push(self, rows):
        sql = ('insert into cache_devGoodsProfit('
               'developer,goodsCode,devDate,goodsStatus,sold,amt,profit,rate,ebaySold,ebayProfit,wishSold,wishProfit,'
               'smtSold,smtProfit,joomSold,joomProfit,amazonSold,amazonProfit,dateFlag,orderTime)'
               'values(%s,%s,%s, %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'
                ' ON DUPLICATE KEY UPDATE sold=values(sold),amt=values(amt),profit=values(profit),'
               'rate=values(rate),ebaySold=values(ebaySold),ebayProfit=values(ebayProfit),wishSold=values(wishSold),'
               'wishProfit=values(wishProfit),smtSold=values(smtSold),joomSold=values(joomSold),joomProfit=values(joomProfit),'
               'amazonSold=values(amazonSold),amazonProfit=values(amazonProfit)'
               )
        self.warehouse_cur.executemany(sql, rows)
        self.warehouse_con.commit()

    @staticmethod
    def date_range(begin_date, end_date):
        dt = datetime.datetime.strptime(begin_date, "%Y-%m-%d")
        date = begin_date[:]
        while date <= end_date:
            dt = dt + datetime.timedelta(1)
            date = dt.strftime("%Y-%m-%d")
            yield date

    def get_month(self, begin_date, end_date):
        month = []
        for date in self.date_range(begin_date, end_date):
            if date[:7] not in month:
                month.append(date[:7])
        return month

    @staticmethod
    def next_month(month):
        (year, month) = month.split('-')
        month = int(month)
        year = int(year)
        if month >= 9 and month < 12:
            month += 1
        elif month >= 1 and month < 9:
            month += 1
            month = '0' + str(month)
        else:
            year += 1
            month = '01'
        return str(year) + '-' + str(month) + '-' + '01'

    def work(self):
        try:
            end_date = str(datetime.datetime.today() - datetime.timedelta(days=1))[:10]
            begin_date = str(datetime.datetime.strptime(end_date[:8] + '01', '%Y-%m-%d'))[:10]
            for date_flag in [0, 1]:
                month = self.get_month(begin_date, end_date)
                for mon in month:
                    begin = mon + '-01'
                    end = self.next_month(mon)
                    rows = self.fetch(begin, end, date_flag)
                    self.push(rows)
                    self.logger.info('success to fetch dev goods profit details between {} and {}'
                                     .format(begin, end))
        except Exception as why:
            self.logger.error('fail to fetch dev goods profit details of {}'.format(why))
        finally:
            self.close()


if __name__ == '__main__':
    worker = Fetcher()
    worker.work()
