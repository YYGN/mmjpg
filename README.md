# mmjpg

通过基本的requests库和beautifulsoup库抓取http：//www.mmjpg.com 网站的图集图片，并存入到mongodb中，以及下载到本地磁盘，由于该网站没有添加任何的反扒虫机制，所以没有添加代理，主要就是使用css选择器找到目标内容，并采用多进程的方式抓取各个图集。
