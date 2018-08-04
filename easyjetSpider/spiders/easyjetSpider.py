import scrapy

import json

import os

import scrapy

from scrapy.spiders import Spider

from scrapy.http import FormRequest

from scrapy.http import Request

from selenium import webdriver

from lxml import etree

from lxml import html

import time

import pyrebase

import pdb

class easyjetSpider(scrapy.Spider):

	name = 'easyjetSpider'

	domain = ''

	history = []

	credentials = []

	db = ''

	def __init__(self):

		self.driver = webdriver.Chrome("./chromedriver.exe")

		config = {

		  	"apiKey": "AIzaSyBV3vFamn4kuSFDtyO80wYl8XNNEN7D_bM",

			"authDomain": "mccrew-e4537.firebaseapp.com",

			"databaseURL": "https://mccrew-e4537.firebaseio.com/",

			"storageBucket": "mccrew-e4537.appspot.com",

			"serviceAccount": "./serviceAccountCredentials.json"
		}

		firebase = pyrebase.initialize_app(config)
		
		auth = firebase.auth()
		
		self.db = firebase.database()

		users = self.db.child("users").get()

		user_list = users.val()['easyJet']

		for key, value in user_list.items():

			self.credentials.append(

				{
					'key' : key,

					'username': value['potalUser'].encode('ascii','ignore').strip(), 

					'password':value['portalPass'].encode('ascii','ignore').replace('"', '').strip()
				}
			)


	def start_requests(self):

		url = 'https://connected.easyjet.com/'

		yield scrapy.Request(url, callback=self.parse)


	def parse(self, response):

		for cred in self.credentials:

			detail = {}

			self.driver.get("https://connected.easyjet.com/my.policy")

			time.sleep(3)

			try:

				self.driver.find_element_by_xpath('//table[@id="IHoptions"]//a[2]').click()

				time.sleep(1)

			except :

				pass

			try:

				self.driver.find_element_by_xpath('//div[@id="newSessionDIV"]//a').click()

				time.sleep(1)
				
			except : 

				pass


			try:

				self.driver.find_element_by_xpath('//table[@id="IHoptions"]//a[2]').click()

				time.sleep(1)

			except :

				pass

			self.driver.find_element_by_name('username').send_keys(cred['username'])

			self.driver.find_element_by_name('password').send_keys(cred['password'])

			self.driver.find_element_by_class_name('credentials_input_submit').click()

			time.sleep(3)

			j1_arr = []

			source = self.driver.page_source.encode("utf8")

			tree = etree.HTML(source)

			travel_list = tree.xpath('//table[@class="widgetTable briefCabinWidgetTable"]//tr[contains(@class, "dataRow")]')


			for travel in travel_list:

				t_model = {}

				t_model['Flight Number'] = self.validate(' '.join(travel.xpath('.//td[@title="Flight Number"]//text()')))
				
				t_model['Aircraft Registration'] = self.validate(' '.join(travel.xpath('.//td[@title="Aircraft Registration"]//text()')))
				
				t_model['Operating Aoc'] = self.validate(' '.join(travel.xpath('.//td[@title="Operating Aoc"]//text()')))
				
				t_model['Aircraft Type'] = self.validate(' '.join(travel.xpath('.//td[@title="Aircraft Type"]//text()')))
				
				t_model['Route'] = self.validate(' '.join(travel.xpath('.//td[@title="Route"]//text()')))
				
				t_model['Standard Time of Departure'] = self.validate(' '.join(travel.xpath('.//td[@title="Standard Time of Departure"]//text()')))
				
				t_model['Standard Time of Arrival'] = self.validate(' '.join(travel.xpath('.//td[@title="Standard Time of Arrival"]//text()'))).replace('\\u25b6', '').strip()
				
				t_model['PAX'] = self.validate(' '.join(travel.xpath('.//td[@title="PAX"]//text()')))
				
				t_model['PRM'] = self.validate(' '.join(travel.xpath('.//td[@title="PRM"]//text()')))
				
				t_model['CHECK'] = self.validate(' '.join(travel.xpath('.//td[@title="CHECK"]//text()')))

				j1_arr.append(t_model)

			url = self.driver.find_element_by_id('0sideNewsUrl').get_attribute('href')

			self.driver.get(url)

			time.sleep(2)

			menu = self.driver.find_element_by_id('ecrewNav')

			self.driver.execute_script("arguments[0].style.visibility = 'visible'; arguments[0].style.height = '1px'; arguments[0].style.width = '1px'; arguments[0].style.opacity = 1", menu)

			self.driver.find_element_by_id('btn_2').click()

			time.sleep(1)

			main_frame = self.driver.find_element_by_id('main_iframe')

			self.driver.switch_to.frame(main_frame)

			self.driver.find_element_by_name('times_formatnormal').send_keys('Local Station')

			self.driver.find_element_by_name('_cont').click()

			time.sleep(3)

			rep_frame = self.driver.find_element_by_name('rep_iframe')

			self.driver.switch_to.frame(rep_frame)

			bottomFrame = self.driver.find_element_by_name('bottomFrame')

			self.driver.switch_to.frame(bottomFrame)

			source = self.driver.page_source.encode("utf8")

			tree = etree.HTML(source)

			calendar = tree.xpath('//table[1]//tr')

			j2_arr = []

			header_list = calendar[5].xpath('.//td')

			for header in header_list:

				item = {}

				item['date'] = self.validate(' '.join(header.xpath('.//text()')))

				item['content'] = ''

				j2_arr.append(item)


			for rec in calendar[6:]:

				columns = rec.xpath('.//td')

				check = ''.join(rec.xpath('.//text()'))

				if 'EXPLANATIONS' in check.upper():

					break

				else:

					ind = 0

					for col in columns[:len(j2_arr)]:

						j2_arr[ind]['content'] += self.validate(' '.join(col.xpath('.//text()'))) + ' '

						ind += 1

			for item in j2_arr:

				res = {

					'date' : item['date'],

					'content' : item['content'].replace('   ', ' ').strip(),
					
				}


			other = tree.xpath('//table[2]//tr')

			o_list = []

			for ind in range(0, len(other)):

				check = ''.join(other[ind].xpath('.//text()'))

				if 'MEMBERS' in check.upper():

					o_list = self.eliminate_space(other[ind+2].xpath('.//text()'))

					break

				ind += 1

			j3_arr = []

			for row in o_list:

				date = row[:2]

				for item in j2_arr:

					if date in item['date']:

						children = self.eliminate_space(row[10:].replace('All', '').split('    '))

						output = {}

						output['date'] = item['date']


						other_arr = []

						for child in children:

							temp = {}

							temp['label'] = child.split('>')[0].strip()

							temp['value'] = child.split('>')[1].strip()

							other_arr.append(temp)

						output['other'] = other_arr

						j3_arr.append(output)

			detail = {

				'flights' : j1_arr,

				'schedule' : j2_arr,

				'other_crew_members' : j3_arr

			}

    		self.db.child('users/easyJet/'+cred['key']+'/data').set(detail)


	def validate(self, item):

		try:

			return item.replace('\n', '').replace('\t','').replace('\r', '').encode('raw-unicode-escape').replace('\xa0', ' ').strip()

		except:

			pass


	def eliminate_space(self, items):

	    tmp = []

	    for item in items:

	        if self.validate(item) != '':

	            tmp.append(self.validate(item))

	    return tmp