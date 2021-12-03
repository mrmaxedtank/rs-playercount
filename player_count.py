#!/usr/bin/python

import os
import sys
import json
import logging
import requests
import time
import pymysql
import pymysql.cursors
import configparser
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from datetime import datetime,timezone
from urllib.request import urlopen
from bs4 import BeautifulSoup

s = requests.Session()
retries = Retry(total=5, backoff_factor=1, status_forcelist=[ 400, 401, 402, 404, 429, 500, 502, 503, 504 ])
s.mount('http://', HTTPAdapter(max_retries=retries))

envi = 'prod'
config = configparser.ConfigParser()
config.read('/home/pi/scripts/rs/player_count/db.conf')
con = pymysql.connect(host = config[envi]['host'], user = config[envi]['user'], password = config[envi]['password'], db = config[envi]['db_name'])

osrs_url = 'https://oldschool.runescape.com/a=13/'
rs3_url = 'https://www.runescape.com/player_count.js?varname=iPlayerCount&callback=jQuery331023439407351407393_1604482624'

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)

def main(args):
	if sys.argv[1] == '--run':
		logging.info('Running check')
		player_count()
		logging.info('------------------------------------------------------------------------')
	else:
		logging.info('Boop')

def player_count():
	logging.info('Function player_count started')

	try:
		with con.cursor() as cur:
			sql = 	'''INSERT into `player_count` (`date`, `rs3`, `osrs`, `total`) 
				VALUES (%s, %s, %s, %s)'''
			rs3 = ''
			osrs = ''
			total = ''
			date = ''
			now = datetime.now()

			with urlopen(rs3_url) as response:
				html_response = response.read()
				encoding = response.headers.get_content_charset('utf-8')
				decoded_html = html_response.decode(encoding)
				tmp_result = decoded_html.split('(')
				tmp_result2 = str(tmp_result[1]).split(')')

			logging.info('Total: ' + str(tmp_result2[0]))
			total = tmp_result2[0]

			with urlopen(osrs_url) as r:
				html_r = r.read()
				parsed_html = BeautifulSoup(html_r, 'html.parser')
				tmp1 = parsed_html.body.find('p', class_='player-count')
				tmp2 = str(tmp1)
				tmp3 = int(''.join(list(filter(str.isdigit, tmp2))))

			logging.info('OSRS: ' + str(tmp3))
			osrs = tmp3

			rs3 = int(total) - int(osrs)
			logging.info('RS3: ' + str(rs3))

			date = now.strftime("%Y-%m-%d %H:%M:%S")
			cur.execute(sql, (date, rs3, osrs, total))
			logging.info('Committing data')
			con.commit()
	finally:
		logging.info('Closing cursor')
		cur.close()

if __name__ == "__main__":
	main(sys.argv[0:])
