# In this script, the oanda api class is created to access the account endpoints
# at instantiation, a session is made with the header updated with authorization and content-Type 

import requests
import cridentials.crid as crid
import pandas as pd
from dateutil import parser
from datetime import datetime as dt


class OandaApi:

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {crid.api_key}',
            'Content-Type': 'application/json'
        })

    def make_request(self, url, verb='get', code=200, params=None, data=None, headers=None):
        '''make_request makes requests to the oanda base url with the following parameters:
        =========
        url: str.
        the url extention to the particular endpoint.

        =========
        verb: str.
        request type

        =========
        code: int.
        status code of the request 200 if the request is okay
        '''
        
        full_url = f'{crid.oanda_url}/{url}'
        try:
            response = None # responce is the variable I want to assign to the response that will be returned from the api
            # it is initialized to None when a request hasn't been made.
            if verb == 'get': # a get request is made when the verb is get
                response = self.session.get(full_url, params=params, data=data, headers=headers)
            if response == None: # if there is a typo or a strange verb is provided then a successful request has not been made 
                # which implies that the response is still None. The function returns false.
                return False, {'error': 'verb not found'}
            if response.status_code == code: # if the status code is 200, it means the request ran successfully
                return True, response.json()# so we return the True and the json file from the api
            else:
                return False, response.json() # if the function returns false, the i want to know the reson for the error
        except Exception as error:
            return False, {'Exception': error}# here the error is returned to enable us fix the error
        
    def get_account_ep(self, ep, data_key): # exploring other endpoint, other sub endpoints will be disocvered 
        # to access these end points, the base url is taken and the account id is attached before the particular sub endpoint
        # get_account_ep will take a subendpoint of the account end point to access the given sub endpoint
        # it will take data_key which holds the value we seek from the response
        url = f'accounts/{crid.account_id}/{ep}'
        ok, data = self.make_request(url);

        if ok == True and data_key in data:
            return data[data_key]
        else:
            print('ERROR get_account_ep()', data)# if the key is not available, this message is returned and the response is printed
            return None
   
    def get_account_summary(self):# this method fetches the account values from the account summary sub end point
        return self.get_account_ep('summary', 'account')
    
    def get_account_instruments(self): # this method gets response from the instrument end. it returns the instruments values from the 
        # json file returned.
        return self.get_account_ep('instruments', 'instruments')
    
    def fetch_candles(self, pair_name, count=10, granularity='H1', price ='MBA', date_f=None, date_t=None):
        url = f'instruments/{pair_name}/candles'
        params = dict(
            granularity = granularity,
            price = price
        )

        if date_f is not None and date_t is not None:
            dateformat = '%Y-%m-%dT%H:%M:%SZ'
            params['from'] = dt.strftime(date_f, dateformat)
            params['to'] = dt.strftime(date_t, dateformat)
        else:
            params['count'] = count

        ok, data = self.make_request(url, params=params)
        if ok == True and 'candles' in data:
            return data['candles']
        else:
            print('ERROR get_account_ep()', params, data)# if the key is not available, this message is returned and the response is printed
            return None
        
    def get_candle_df(self, pair_name, **kwargs):

        data = self.fetch_candles(pair_name, **kwargs)

        if data is None:
            return None
        if  len(data) == 0: # in case the returned data is empty, the function should return an empty dataframe should be etrurned.
            return pd.DataFrame()  
         
        prices = ['mid', 'bid', 'ask'] # to flatten the prices, i will over them and 
        ohlc = ['o', 'h', 'l', 'c'] # extract thr ohlc indivdiually
        
        final_data = [] # each of the candlesticks properties are appended in this list
        
        for item in data:
            if item['complete'] == False:
                continue
            dict_obj = {}
            dict_obj['time'] = parser.parse(item['time'])
            dict_obj['volume'] = item['volume']
            for price in prices:
                if price in item:
                    for _ in ohlc:
                        dict_obj[f'{price}_{_}'] = float(item[f'{price}'][f'{_}'])
            final_data.append(dict_obj)
        return pd.DataFrame(final_data)

