import os
import platform
import urllib.request
# import urllib.parse
from urllib.request import Request, urlopen
from urllib.error import URLError
# Use request for certain sites due to 403 forbidden in urllib
# may be related to redirection of url
import requests
from enum import Enum
import json
from datetime import datetime, time
from os import path, getenv, system
import sys
from time import sleep
import webbrowser
import psutil
import subprocess
# import custom logger
import logconfig
import requests
from dotenv import load_dotenv
import re
from bs4 import BeautifulSoup
import random

from selenium import webdriver
from selenium.webdriver.firefox.options import Options

logconfig.logger.info('** info logging enabled **')

load_dotenv()
USE_SELENIUM = False
USE_DISCORD_HOOK = False
WEBDRIVER_PATH = path.normpath(getenv('WEBDRIVER_PATH'))
DISCORD_WEBHOOK_URL = getenv('DISCORD_WEBHOOK_URL')
ALERT_DELAY = int(getenv('ALERT_DELAY'))
MIN_DELAY = int(getenv('MIN_DELAY'))
MAX_DELAY = int(getenv('MAX_DELAY'))
OPEN_WEB_BROWSER = getenv('OPEN_WEB_BROWSER') == 'true'

platform = platform.system()
PLT_LIN = "Linux"
PLT_MAC = "Darwin"

##
# Add More Sources
# - Office Depot
# - Staples
#
##


class Methods(str, Enum):
    # Adding GET_REQUEST for urls that may return 403 forbidden when using urllib

    GET_SELENIUM = "GET_SELENIUM"
    GET_URLLIB = "GET_URLLIB"
    GET_API = "GET_API"
    GET_REQUEST = "GET_REQUEST"


# Selenium Setup
if WEBDRIVER_PATH:
    USE_SELENIUM = True
    print("Enabling Selenium... ", end='')
    # from selenium import webdriver
    # from selenium.webdriver.firefox.options import Options

    options = Options()
    # Note: forcing headless mode here but on systems that have GUI this can be enabled and user will have to quit each running instance
    # check running processes to see if firefox is being orphaned
    options.headless = True
    # NOTE: adding firefox profile and dom disable before unload to see if it fixes orphaned firefox processes
    # running out of memory due to this
    # https://stackoverflow.com/questions/48703734/why-does-the-python-selenium-webdriver-quit-not-quit
    # above link also has a function for checking and killing firefox processes
    options.set_preference("dom.disable_beforeunload", True)

    driver = webdriver.Firefox(options=options, executable_path=WEBDRIVER_PATH)
    reload_count = 0
    print("Done!")


def discord_notification(site_info, url):
    # NOTE: for now statically mapping dictionary key values, just product title and
    if USE_DISCORD_HOOK:
        data = {
            "content": "{} in stock at {}".format(site_info['product_title'],
                                                  url) + "\r\n buy link: " + site_info['buy_url'],
            "username": "\r\n\r\nIn Stock Alert!\r\n\n"}
        result = requests.post(DISCORD_WEBHOOK_URL, data=json.dumps(data), headers={"Content-Type": "application/json"})
        try:
            result.raise_for_status()
        except requests.exceptions.HTTPError as err:
            print(err)
        else:
            print("Payload delivered successfully, code {}.".format(result.status_code))


def os_notification(title, text):
    if platform == PLT_MAC:
        system("""
                  osascript -e 'display notification "{}" with title "{}"'
                  """.format(text, title))
        system('afplay /System/Library/Sounds/Glass.aiff')
        system('say "{}"'.format(title))
    elif platform == PLT_LIN:
        try:
            icon_path = path.realpath('icon.ico')
            system('notify-send "{}" "{}" -i {}'.format(title, text, icon_path))
        except:
            # No system support for notify-send
            pass


if DISCORD_WEBHOOK_URL:
    USE_DISCORD_HOOK = True
    print('Enabled Discord Web Hook.')


def alert(site, site_info):
    # TODO: Add Info Gathered From parse_site and pass into this function for notifications
    # For example, Amazon Buying Options URL
    product = site.get('name')
    print("{} IN STOCK".format(product))
    print(site.get('url'))
    if OPEN_WEB_BROWSER:
        webbrowser.open(site.get('url'), new=1)
    # NOTE: running code on Ubuntu 18.04 in headless mode without GUI so disable
    # os_notification("{} IN STOCK".format(product), site.get('url'))
    site_info['product_title'] = product
    discord_notification(site_info, site.get('url'))
    sleep(ALERT_DELAY)


def parse_site(site, html):
    print('parse site')
    soup = BeautifulSoup(html, 'html.parser')
    # TODO: Change parse parameter to key value pairs so each data point can be labeled
    # Add an additional array value for parsing trigger methods
    parse_ids = site.get('parse')
    print(parse_ids)
    print(parse_ids['type'])
    # remove type key from dict, remaining keys for parsing
    type = parse_ids.pop('type')
    info_dict = {}
    if(type == 'amazon'):
        for key, value in parse_ids.items():
            # print(k, v)
            tag = soup.find(value[0], id=value[2])
            tag_attr = tag[value[1]]
            link = value[3] + tag_attr
            info_dict[key] = link
            print(key + ':  -> : ', link)
    elif(type == 'bestbuy'):
        print('bestbuy hit!')
        for key, value in parse_ids.items():
            print("k: ", key + ": " + value)
            button_div = soup.find_all("div", class_=value)

            #tag = site.get('tag')
            #add_cart = 'Add To Cart'
            #index = button_div.upper().find(tag.upper())

            for tag in button_div:
                for value in tag:
                    print(value)
                    tag = site.get('tag')
                    add_cart = 'Add To Cart'
                    value_string = str(value)
                    index = value_string.upper().find(add_cart.upper())
                    print(index)

            # use_href = tag.find_all('use', href=True)
            # print(use_href)
            # for value in use_href:
            #     print(value)

    return info_dict


def find_stock_in_html(site, site_html):
    #
    # TODO: Refactor Code to manage differences between sites
    # bestbuy.com had Add To Cart in the comments thus triggering false positive
    # Look into finding divs for the Add To Cart button and then searching for Add To Cart within the div

    # NOTE: For tag phrases add support for multiple phrases with a JSON Array for tags
    # create array parsed by pipe and check all phrases in loop
    # For Example Amazon Uses: Add to Cart and See All Buying Options
    # Amazon has cards in stock that are marked up from retails price
    # NOTE: With bs4 capture the See All Buying Options html link and add it to Discord text alert
    in_stock = False
    tags = site.get('tags')
    print(":: site tags -> ", tags)
    alert_status = site.get('alert')
    # .find does a basic search through all html for the tagss or phrase
    # for some sites look into bs4 for finding in DOM
    for tag in tags:
        print(tag)
        index = site_html.upper().find(tag.upper())
        print('index: ', index)
        if index >= 0:
            in_stock = True
            # parse for additional info
            # TODO: Check if sites are parsing with empty arrays, check length or find other method to prevent this
            site_info = {}
            if site.get('parse') is not None and len(site.get('parse')) > 0:
                site_info = parse_site(site, site_html)

            # send alerts if True
            if site.get('alert'):
                print("\r ** post alert ** \r")
                alert(site, site_info)
        print('in stock: ', in_stock)


def request_get(site):
    url = site.get('url')
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko Chrome/83.0.4103.97 Safari/537.36"}
    site_request = requests.get(url, headers=headers)
    site_html = site_request.text
    find_stock_in_html(site, site_html)
    html_stripped = re.sub('<[^<]+?>', '', site_html)
    logconfig.logger.info(html_stripped)
    print('requests status code: ', site_request.status_code)
    logconfig.logger.info(site_request.content)


def selenium_get(site):
    global driver
    global reload_count

    driver.get(site.get('url'))
    site_html = driver.page_source
    find_stock_in_html(site, site_html)
    logconfig.logger.info(site_html)
    # TODO: See if there is a way to get the web status code from Seleium after retrieving page content
    logconfig.logger.info("selenium_get -> " + str(site_html))
    # TODO: Running out of memory with script running every hour
    # remove reload code below and close and quit driver
    reload_count += 1
    # NOTE: Was getting a reload error without this for Amazon 3060 stock check
    # Make sure
    if reload_count == 10:
        reload_count = 0
        print('** selenium reload count of 10 reached **')
        driver.close()
        driver.quit()
        # driver = webdriver.Firefox(options=options, executable_path=WEBDRIVER_PATH)

    # driver.close()
    # driver.quit()
    return site_html


def urllib_get(site):
    # https: // docs.python.org/3/howto/urllib2.html
    html = ''
    url = site.get('url')
    # NOTE: data param set to None
    request = Request(url, data=None, headers={
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'})
    # recommended URLError dump
    try:
        response = urllib.request.urlopen(request, timeout=30)
        status_code = response.getcode()
        print('urllib status code:', status_code)
        html_bytes = response.read()
        site_html = html_bytes.decode("utf-8")
        # logconfig.logger.info(site_html)
        find_stock_in_html(site, site_html)
    except URLError as e:
        if hasattr(e, 'reason'):
            print('** URLError:', e.reason)
        elif hasattr(e, 'code'):
            print('The server couldn\'t fulfill the request.')
            print('Error code: ', e.code)
    else:
        logconfig.logger.info("** no response from URLError**")

    return html


# NOTE: referencing sites.json from the current directory where the script resides
# may need to set full path to file as what was done with the logging file
with open('sites.json', 'r') as f:
    sites = json.load(f)
    # print(sites)

for site in sites:
    # Add ENUM Switch here
    site_enabled = site.get('enabled')
    if(site_enabled):
        print(site.get('url'))
        if site.get('method') == Methods.GET_URLLIB:
            html = urllib_get(site)
        elif site.get('method') == Methods.GET_REQUEST:
            html = request_get(site)
        elif site.get('method') == Methods.GET_SELENIUM:

            html = selenium_get(site)
        else:
            print('* default hit for enum')
        print("\r\n =========== \r\n")
    base_sleep = 1
    total_sleep = base_sleep + random.uniform(MIN_DELAY, MAX_DELAY)
    sleep(total_sleep)

sleep(5)

options = Options()
options.headless = True
options.set_preference("dom.disable_beforeunload", True)
driver = webdriver.Firefox(options=options, executable_path=WEBDRIVER_PATH)
driver_process = psutil.Process(driver.service.process.pid)

if driver_process.is_running():
    print("driver is running")

    firefox_process = driver_process.children()
    if firefox_process:
        firefox_process = firefox_process[0]

        if firefox_process.is_running():
            print("Firefox is still running, we can quit")
            driver.quit()
            # firefox browser is still running in headless mode
            # TODO: see if there is a way to stop run away firefox processes without killall call
            if OPEN_WEB_BROWSER == False:
                # only killall on setups in headless mode, otherwise all instances of firefox will be killed
                # so if you have another version of firefox running it will be killed
                print('* headless mode enabled - killall *')
                process = subprocess.run(['killall', 'firefox'],
                                         stdout=subprocess.PIPE,
                                         universal_newlines=True)

        else:
            print("Firefox is dead, can't quit. Let's kill the driver")
            firefox_process.kill()
    else:
        print("driver has died")
