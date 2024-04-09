#  in this script we are going to write a code that turns the tradable instruments from the instrument endpoint
#  into a python dictionary object.

from models.instruments import Instrument
import json

class InstrumentCollection:
    FILENAME = 'instruments.json' # intialize the filename to instruments.json, a name i want to save the file with
    # api_keys: the keys housing the value i need
    API_KEYS = [
        'name', 
        'type', 
        'displayName', 
        'pipLocation', 
        'displayPrecision', 
        'tradeUnitsPrecision',
        'marginRate'
    ]

    def __init__(self):
        self.instruments_dict = {} # at instantiation, the instruments_dict is initialized to empty

    def CreateFile(self, data, path):
        #  to create the dict object, Createfile takes the data returned from the instruments endpoint of the oandaapi class
        #  as follows:
        if data == None: # when the response from the instruments endpoint is None, the string below is printed
            print('Instrument file creation failed')
            return
        
        instruments_dict = {}
        for i in data:
            key = i['name']
            instruments_dict[key] = {k: i[k] for k in self.API_KEYS}

        fileName =f'{path}/{self.FILENAME}'
        with open(fileName, 'w') as f:
            f.write(json.dumps(instruments_dict, indent=2))
            

    def LoadInstruments(self, path):
        self.instruments_dict = {}
        fileName =f'{path}/{self.FILENAME}'
        with open(fileName, 'r') as f:
            data = json.loads(f.read())
            for k, v in data.items():
                self.instruments_dict[k] = Instrument.FromApiObject(v)

    def PrintInstruments(self):
        [print(k,v) for k, v in self.instruments_dict.items()]
        print(self.instruments_dict.keys)

instrumentCollection = InstrumentCollection()

