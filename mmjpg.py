# -*- coding: utf-8 -*-

import re
from multiprocessing import Pool
import os
import pymongo
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from requests.exceptions import *
from hashlib import md5

base_url = "httP://www.mmjpg.com"

headers = {
    'UserAgent': UserAgent().random
}

mongo_cli = pymongo.MongoClient(host='localhost')
mongo_db = mongo_cli['mmjpg']

def get_html(url=None):
    """发送请求并取得response"""
    url = url if url else base_url
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            # print('*****获取页面成功*****')
            response.encoding = response.apparent_encoding
            return response.text
        else:
            return None
    except (HTTPError, Timeout, ConnectionError, Exception) as e:
        print('错误消息',e)

def parse_html(html):
    """获取所有页面的html"""
    soup = BeautifulSoup(html, 'lxml')
    pages = int(soup.select('em.info')[0].get_text()[1:3])    # 获取总共的页数信息
    # print(pages)
    for page in range(1,pages+1):
        url = base_url + '/home/' + repr(page)  # 组合URL链接
        yield get_html(url)

def parse_detail(html):
    """获取每个页面中图集的链接"""
    soup = BeautifulSoup(html, 'lxml')
    elements = soup.select('div.pic ul li a')
    # print(elements)
    for element in elements:
        yield element.get('href')

def send_args(func):
    from functools import wraps
    @wraps(func)
    def wrapper(args):
        if isinstance(args, dict):
            return func(**args)
        else:
            return func(*args)
    return wrapper

@send_args
def parse_single_page(url, link, images=None, referer=None):
    """解析单个图集"""
    if images is None:
        images = []
    if referer is None:
        referer = []
    referer.append(url)
    html = get_html(url)
    # print(html)    # 取得单个图集的html
    soup = BeautifulSoup(html, 'lxml')
    title = soup.select('div.article h2')[0].get_text()
    image_url = soup.select('div.content a img')[0].get('src')
    print(title, image_url)
    images.append(image_url)
    if soup.select('div.page a')[-1].get_text() == '下一张':
        next_page = soup.select('div.page a')[-1].get('href')
        if next_page:
            pattern = re.search(r'/.*?/.*?(/\d+$)', next_page).group(1)
            next_url = link + pattern
            print('正在前往页面', next_url)
            # 跳转下一页
            parse_single_page_diff(next_url, link, images, title, referer)
            # print('1')
            url_referer = []
            for url, referer in zip(images, referer):
                url_referer.append([url, referer])
            date = {
                'title': title,
                'url_referer': url_referer
            }
            save_image(date)

def parse_single_page_diff(url, link, images, title,referer):
    html = get_html(url)
    # print(html)    # 取得单个图集的html
    soup = BeautifulSoup(html, 'lxml')
    image_url = soup.select('div.content a img')[0].get('src')
    # print(title, image_url)
    referer.append(url)
    images.append(image_url)
    if soup.select('div.page a')[-1].get_text() == '下一张':
        next_page = soup.select('div.page a')[-1].get('href')
        if next_page:
            pattern = re.search(r'/.*?/.*?(/\d+$)', next_page).group(1)
            next_url = link + pattern
            print('正在前往页面', next_url)
            # 跳转下一页
            parse_single_page_diff(next_url, link, images, title, referer)

def save_image(date):
    if mongo_db['items'].update({'title': date['title']}, {'$set': date}, True):
        print('存入mongodb成功')
    flode_name = date.get('title')
    docs = date.get('url_referer')
    file_path = '/media/gbc/Download/mmjpg/' + flode_name + '/'
    if not os.path.exists(file_path):
        os.mkdir(file_path)
    for doc in docs:
        try:
            response = requests.get(doc[0], headers={'Referer': doc[1]})
            if response.status_code == 200:
                content = response.content
                file_name = md5(content).hexdigest() + '.jpg'
                if not os.path.exists(file_name):
                    with open(file_path + file_name, 'wb') as f:
                        print('正在保存图片中 ', file_name)
                        f.write(content)
                        f.close()
                else:
                    print('图片已经存在')
        except:
            pass

def spider():
    try:
        html = get_html()
        if html:
            htmls = parse_html(html)    # 所有页面的html
            for html in htmls:
                urls = parse_detail(html)   # 网站上所有的图集链接
                if urls:
                    urls = list(urls)[::2]
                    loop = Pool(6)
                    loop.map(parse_single_page, zip(urls, urls))
                    loop.close()
                    # loop.join()
    finally:
        mongo_cli.close()
                # for url in list(urls)[::2]:
                #     result = parse_single_page(url, link=url)
                #     print(result)
                    # if result:
                    #     save_to_mongo(result)





if __name__ == '__main__':
    spider()