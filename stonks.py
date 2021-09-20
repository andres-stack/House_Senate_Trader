import urllib.request
from urllib.request import urlopen
from bs4 import BeautifulSoup
import requests
import requests
import json
import datetime
from td.client import TDClient
import pickle
import yahoo_fin.stock_info as si
from yahoo_fin import stock_info as si
import schedule
from splinter import Browser
import time

myPortfolio = {}
CONSUMER_KEY= #consumer_Key
REDIRECT_URI = #Redirect URI
client_id = #client_id

def isThereTrade():

    x = datetime.datetime.now()

    year = str(x.year)
    month = str('%02d' % x.month)
    month = str('%02d' % 4)
    day = str('%02d' % 12)
    #day = str('%02d' % x.day)

    url2 = "https://senate-stock-watcher-data.s3.amazonaws.com/"

    dailyReportList = []

    xml_data = requests.get(url2).content

    xml = BeautifulSoup(xml_data, "lxml")

    for i in xml.find_all("key"):
        dailyReportList.append(i)

    string_ints = [str(int) for int in dailyReportList]

    dailyReport = ""

    dailyReport += "<key>data/transaction_report_for_"
    dailyReport += month
    dailyReport += "_"
    dailyReport += day
    dailyReport += "_"
    dailyReport += year
    dailyReport += ".json"
    dailyReport += "</key>"

    #if there is a stock trade today and it is a stock then buy the stock
    if dailyReport in string_ints:

        url = "https://senate-stock-watcher-data.s3.amazonaws.com/data/transaction_report_for_"

        url += month
        url += "_"
        url += day
        url += "_"
        url += year
        url += ".json"

        print(url)

        r = requests.get(url)
        x = r.json()
        y = json.dumps(x)
        z = json.loads(y)[0]
        i = 0
        f = 0
        stock = ""

        for dictionary in z['transactions']:
            i = i+1

        print(i)

        while f < i:
            if z['transactions'][f]['asset_type'] == "Stock" and (z['transactions'][f]['type'] == "Purchase"):
                stock = (z['transactions'][f]['asset_description'])
                break

            f = f+1
        if len(stock) > 1:
            print(stock)

            #loop through the stock string and turn into symbol
            constock = stock.replace(",", "")
            constock = constock.replace(".", "")
            print(constock)

            #turn stock name into ticker/symbol
            res = requests.get(f'https://www.alphavantage.co/query?function=SYMBOL_SEARCH&keywords={constock}&apikey=') #add API key
            response = res.json()
            print(response)
            symbol = response["bestMatches"][0]["1. symbol"]

            #dont buy if i already own the stock
            counter = 0

            infile = open('portfolio', 'rb')
            myPortfolio = pickle.load(infile)
            infile.close()

            for key in myPortfolio:
                if key == symbol:
                    counter = counter + 1
                else:
                    counter = counter + 0

            outfile = open("portfolio", "wb")
            pickle.dump(myPortfolio, outfile)
            outfile.close()

            if counter == 0:
                # see i can buy stock with my available chash
                executable_path = {'/Users/andrestrujillo/PycharmProjects/stonks/venv/chromedriver 5'}
                browser = Browser('chrome', **executable_path, headless=False)

                # define the components to build a URL
                method = 'GET'
                url = 'https://auth.tdameritrade.com/auth?'
                client_code = client_id + '@AMER.OAUTHAP'
                payload = {'response_type': 'code', 'redirect_uri': REDIRECT_URI, 'client_id': client_code}

                # build the URL and store it in a new variable
                p = requests.Request(method, url, params=payload).prepare()
                myurl = p.url

                # go to the URL
                browser.visit(myurl)

                # define items to fillout form
                payload = {'username': "",
                           'password': ""} #add username and password

                # fill out each part of the form and click submit
                username = browser.find_by_id("username0").first.fill(payload['username'])
                password = browser.find_by_id("password1").first.fill(payload['password'])
                submit = browser.find_by_id("accept").first.click()

                # click the Accept terms button
                browser.find_by_id("accept").first.click()
                browser.find_by_xpath('//*[@id="authform"]/main/details/summary').first.click()
                browser.find_by_xpath('//*[@id="stepup_secretquestion0"]/div/input').first.click()
                browser.find_by_xpath('//*[@id="secretquestion0"]').first.fill(':7PP67Y^,Rr"Asu>')
                browser.find_by_xpath('//*[@id="accept"]').first.click()
                browser.find_by_xpath('//*[@id="stepup_trustthisdevice0"]/div[1]/label').first.click()
                browser.find_by_xpath('//*[@id="accept"]').first.click()
                browser.find_by_xpath('//*[@id="accept"]').first.click()

                # give it a second, then grab the url
                time.sleep(3)

                new_url = browser.url

                # grab the part we need, and decode it.
                parse_url = urllib.parse.unquote(new_url.split('code=')[1])

                # close the browser
                browser.quit()

                # THE AUTHENTICATION ENDPOINT

                # define the endpoint
                url = r"https://api.tdameritrade.com/v1/oauth2/token"

                # define the headers
                headers = {"Content-Type": "application/x-www-form-urlencoded"}

                # define the payload
                payload = {'grant_type': 'authorization_code',
                           'access_type': 'offline',
                           'code': parse_url,
                           'client_id': client_id,
                           'redirect_uri': REDIRECT_URI}

                # post the data to get the token
                authReply = requests.post(r'https://api.tdameritrade.com/v1/oauth2/token', headers=headers,
                                          data=payload)

                # convert it to a dictionary
                decoded_content = authReply.json()

                # grab the access_token
                access_token = decoded_content['access_token']
                headers = {'Authorization': "Bearer {}".format(access_token)}

                endpoint = r"https://api.tdameritrade.com/v1/accounts"
                content = requests.get(url=endpoint, headers=headers)
                data = content.json()
                print(data)
                cash = data[0]['securitiesAccount']['initialBalances']['cashBalance']
                print(cash)

                # buy stock if i have eneogh cash
                if (si.get_live_price(symbol) < cash):
                    # add the symbol and price to dictionary
                    infile = open('portfolio', 'rb')
                    myPortfolio = pickle.load(infile)
                    infile.close()

                    myPortfolio[symbol] = si.get_live_price(symbol)
                    # myPortfolio.clear()

                    outfile = open("portfolio", "wb")
                    pickle.dump(myPortfolio, outfile)
                    outfile.close()

                    print(myPortfolio)

                    # actually buying the stock
                    header = {'Authorization': "Bearer {}".format(access_token),
                              "Content-Type": "application/json"}

                    # define the endpoint for Saved orders, including your account ID
                    endpoint = r"https://api.tdameritrade.com/v1/accounts/{}/orders".format(234854886)

                    # define the payload, in JSON format
                    payload = {'orderType': 'MARKET',
                               'session': 'NORMAL',
                               'duration': 'DAY',
                               'orderStrategyType': 'SINGLE',
                               'orderLegCollection': [{'instruction': 'Buy', 'quantity': 1,
                                                       'instrument': {'symbol': symbol, 'assetType': 'EQUITY'}}]}
                    # make a post, NOTE WE'VE CHANGED DATA TO JSON AND ARE USING POST
                    content = requests.post(url=endpoint, json=payload, headers=header)

                    # show the status code, we want 200
                    content.status_code




                else:
                    print("this stock is too expensive")




            else:
                print("i already own this stock")

        else:
                print("the transaction is either not a stock or a sale")

    else:
        print("No Senators have bought or sold stocks today")



def shouldSell():
    infile = open('portfolio', 'rb')
    myPortfolio = pickle.load(infile)
    infile.close()

    #loop through
    for key in list(myPortfolio):
        print(myPortfolio)
        percentIncrease = myPortfolio[key] * 1.2 
        if percentIncrease <= si.get_live_price(key):
            # see i can buy stock with my available chash
            executable_path = {'executable_path': r'/Users/andrestrujillo/PycharmProjects/stonks/chromedriver 5'}
            browser = Browser('chrome', **executable_path, headless=False)

            # define the components to build a URL
            method = 'GET'
            url = 'https://auth.tdameritrade.com/auth?'
            client_code = client_id + '@AMER.OAUTHAP'
            payload = {'response_type': 'code', 'redirect_uri': REDIRECT_URI, 'client_id': client_code}

            # build the URL and store it in a new variable
            p = requests.Request(method, url, params=payload).prepare()
            myurl = p.url

            # go to the URL
            browser.visit(myurl)

            # define items to fillout form
            payload = {'username': "",
                       'password': ""} #add username and password

            # fill out each part of the form and click submit
            username = browser.find_by_id("username0").first.fill(payload['username'])
            password = browser.find_by_id("password1").first.fill(payload['password'])
            submit = browser.find_by_id("accept").first.click()

            # click the Accept terms button
            browser.find_by_id("accept").first.click()
            browser.find_by_xpath('//*[@id="authform"]/main/details/summary').first.click()
            browser.find_by_xpath('//*[@id="stepup_secretquestion0"]/div/input').first.click()
            browser.find_by_xpath('//*[@id="secretquestion0"]').first.fill(':7PP67Y^,Rr"Asu>')
            browser.find_by_xpath('//*[@id="accept"]').first.click()
            browser.find_by_xpath('//*[@id="stepup_trustthisdevice0"]/div[1]/label').first.click()
            browser.find_by_xpath('//*[@id="accept"]').first.click()
            browser.find_by_xpath('//*[@id="accept"]').first.click()

            # give it a second, then grab the url
            time.sleep(3)

            new_url = browser.url

            # grab the part we need, and decode it.
            parse_url = urllib.parse.unquote(new_url.split('code=')[1])

            # close the browser
            browser.quit()

            # THE AUTHENTICATION ENDPOINT

            # define the endpoint
            url = r"https://api.tdameritrade.com/v1/oauth2/token"

            # define the headers
            headers = {"Content-Type": "application/x-www-form-urlencoded"}

            # define the payload
            payload = {'grant_type': 'authorization_code',
                       'access_type': 'offline',
                       'code': parse_url,
                       'client_id': client_id,
                       'redirect_uri': REDIRECT_URI}

            # post the data to get the token
            authReply = requests.post(r'https://api.tdameritrade.com/v1/oauth2/token', headers=headers, data=payload)

            # convert it to a dictionary
            decoded_content = authReply.json()

            # grab the access_token
            access_token = decoded_content['access_token']

            # actually selling
            header = {'Authorization': "Bearer {}".format(access_token),
                      "Content-Type": "application/json"}

            # define the endpoint for Saved orders, including your account ID
            endpoint = r"https://api.tdameritrade.com/v1/accounts/{}/orders".format(234854886)

            # define the payload, in JSON format
            payload = {'orderType': 'MARKET',
                       'session': 'NORMAL',
                       'duration': 'DAY',
                       'orderStrategyType': 'SINGLE',
                       'orderLegCollection': [{'instruction': 'SELL', 'quantity': 1,
                                               'instrument': {'symbol': key, 'assetType': 'EQUITY'}}]}
            # make a post
            content = requests.post(url=endpoint, json=payload, headers=header)

            # show the status code, we want 200
            content.status_code

            #once the stock is sold delete it
            del myPortfolio[key]
            outfile = open("portfolio", "wb")
            pickle.dump(myPortfolio, outfile)
            outfile.close()

def checkinPortfolio():
    schedule.every(10).seconds.until("00:37").do(shouldSell)
#actual time is 15:30

schedule.every().monday.at("18:28").do(isThereTrade)
schedule.every().tuesday.at("20:00").do(isThereTrade)
schedule.every().wednesday.at("20:00").do(isThereTrade)
schedule.every().thursday.at("20:00").do(isThereTrade)
schedule.every().friday.at("20:00").do(isThereTrade)

schedule.every().monday.at("00:36").do(checkinPortfolio)
schedule.every().tuesday.at("08:30").do(checkinPortfolio)
schedule.every().wednesday.at("08:30").do(checkinPortfolio)
schedule.every().thursday.at("08:30").do(checkinPortfolio)
schedule.every().friday.at("08:30").do(checkinPortfolio)

while True:
    schedule.run_pending()
    time.sleep(1)