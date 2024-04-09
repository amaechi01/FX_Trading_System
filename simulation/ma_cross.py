import pandas as pd
import os.path
from simulation.ma_excel import create_ma_res
from infrastructure.instrument_collection import instrumentCollection as ic

class MAResult:
    '''
    this class is instantiated with a dataframe, instrument, a long moving average, a short moving average and a granularity.
    at the point of instantiation, the result_ob method is used to create a dict object holding important information from the dataframe. this
    dict object can be access using the result atrribute of the class.
    '''
    def __init__(self, df_trades, pairname, ma_l, ma_s, granularity):
        self.pairname = pairname
        self.df_trades = df_trades
        self.ma_s = ma_s
        self.ma_l = ma_l
        self.granularity = granularity
        self.result = self.result_ob()

    def __repr__(self):
        return str(self.result)

    def result_ob(self):
        return dict(
            pair = self.pairname,
            num_trades = self.df_trades.shape[0],
            total_gain = int(self.df_trades['Gain'].sum()),
            min_gain = int(self.df_trades['Gain'].min()),
            average_gain = int(self.df_trades['Gain'].mean()),
            max_gain = int(self.df_trades['Gain'].max()),
            ma_l = self.ma_l,
            ma_s = self.ma_s,
            cross= f'{self.ma_s}_{self.ma_l}',
            granularity = self.granularity
        )
        

BUY = 1
SELL = -1
NONE = 0

get_ma_col = lambda x: f'MA_{x}'
add_cross = lambda x: f'{x.ma_s}_{x.ma_l}'

def load_price_data(pair, granularity, ma_list):
    '''
    load_price_data take a pair, a list of granularity and a list of moving average.
    the elements of the lists are used to form moving average columns in the dataset.
    '''
    df = pd.read_pickle(f'./data/{pair}_{granularity}.pkl')
    for ma in ma_list:
        df[get_ma_col(ma)] = df.mid_c.rolling(window=ma).mean()
    df.dropna(inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df

def is_trade(df):
    # detects the trades when there is a crossover
    if df['Delta'] >= 0 and df['Delta_Prev'] < 0:
        return BUY
    elif df['Delta'] < 0 and df['Delta_Prev'] >= 0:
        return SELL
    return NONE

def get_trades(df_analysis, instrument, granularity):
    '''get_tarde uses the instrument.pipLocation to calculate the pips lost or gained by the ma crossover'''
    df_trades = df_analysis[df_analysis['Trades']!=NONE].copy()
    df_trades['Diff'] = df_trades['mid_c'].diff().shift(-1)
    df_trades.fillna(0, inplace=True)
    df_trades['Gain'] = df_trades['Diff'] / instrument.pipLocation
    df_trades['Gain'] = df_trades['Gain'] * df_trades['Trades']
    df_trades['Granularity'] = granularity
    df_trades['Pair'] = instrument.name
    df_trades['Gain_C'] = df_trades['Gain'].cumsum()
    return df_trades

def assess_pair(price_data, ma_l, ma_s, instrument, granularity):
    '''assess_pair takes a dataframe, an ma_long, ma_short, the instrument and the granularity. It uses the ma values to setup the ma-cross over 
    principle and then detects trades using the said ma values.

    To further prepare the dataset, assess_pair uses get_trade to the ma_cross over trades using the provided ma values

    The resulting dataframe is used to return a MAResult object.
    '''
    df_analysis = price_data.copy()
    df_analysis['Delta'] = df_analysis[ma_s] - df_analysis[ma_l]
    df_analysis['Delta_Prev'] = df_analysis['Delta'].shift(1)
    df_analysis['Trades'] = df_analysis.apply(is_trade, axis=1)
    df_trade = get_trades(df_analysis, instrument, granularity)
    df_trade['ma_l'] = ma_l
    df_trade['ma_s'] = ma_s
    df_trade['Cross'] = df_trade.apply(add_cross, axis=1)
    return MAResult(
        df_trade,
        instrument.name,
        ma_l,
        ma_s,
        granularity
    )
# analyse _pair is the function that will be fed into run_ma_sim. the function will take an instrument, the granukarity in or oder to read the 
# dataset that corresponds to the pair and granularity. It takes the lists of the ma_long and ma_short and combine them.

def append_df_to_file(df, filename):
    '''                                                                                                                                                                                                                                                                                                                                                                                         
    append_df_to_file takes a dataframe and its name and checks if the file is already in the path.
    if it is, the existing file and the new dataframe are concatinated. if it is not there, the dataset is created using the dataframe.
    '''
    if os.path.isfile(filename):
        fd = pd.read_pickle(filename)
        df = pd.concat([fd, df])
    df.reset_index(inplace=True, drop=True)
    df.to_pickle(filename)
    print(filename, df.shape)
    print(df.tail(2))

def get_fullname(filepath, filename):
    '''get_fullname provides full path where we want to save the dataset and the anme of the dataset'''
    return f'{filepath}/{filename}.pkl'

def process_macro(result_list, filename):
    '''process_trades uses the result attribute of the MAResult class to access the result dict of the pairs and 
        creates a list of them with is used to create a dataframe which is saved using append_df_to_file to save the resulting dataset
    '''
    rl = [x.result for x in result_list]
    df = pd.DataFrame.from_dict(rl)
    append_df_to_file(df, filename)

def process_trades(result_list, filename):
    '''process_trades uses the df_trades attribute of the MAResult class to access the trade datafram of the pairs and concatinates 
        and uses append_df_to_file to save the resulting dataset
    '''
    df = pd.concat([x.df_trades for x in result_list])
    append_df_to_file(df, filename)

def process_results(result_list, filepath):
    '''process_result uses two functions namely: 
    process_macro and process_trades to save the data from the MAResult class and trade datasets from get_trades respectively.
    '''
    process_macro(result_list, get_fullname(filepath, 'ma_res'))
    process_trades(result_list, get_fullname(filepath, 'ma_trades'))
    # rl = [x.result for x in result_list]
    # df = pd.DataFrame.from_dict(rl)
    # print(df)
    # print(result_list[0].df_trades.head(2))

def analyse_pair(instrument, granularity, ma_long, ma_short, filepath):
    '''analyze_pair takes five arguments :
    instrument: a tradable instrument.
    granularity: the granlarity of the pair.
    ma_long: list of the long moving average.
    ma_short: list of short moving avaerage,
    filepath: path to the data folder.

    analyse_pair makes a set of ma_long and ma_short and makes a list it. it then loads the pair corresponding to the provided granularity
    using load_price_data.

    analyse_pair iterates through all the values of the MAs and checks to filter out cases where ma_long is shorter than ma_short to exclude them
    and only makes use of the cases where ma_long is actually longer than ma_long.

    it thn uses assess_pair to analyse the pair and the result is appened in result_list.

    process_results is used to save the result of the analysis
    '''
    ma_list = set(ma_long + ma_short)
    pair = instrument.name

    #the ma_list is fed into load_price_data where the dataset is finally read in having the columns of all the MAs
    price_data = load_price_data(pair, granularity, ma_list)
    
    #
    result_list = []
    for ma_l in ma_long:
        for ma_s in ma_list:
            if ma_l <= ma_s:
                continue
            ma_result = assess_pair(
                price_data,
                get_ma_col(ma_l),
                get_ma_col(ma_s),
                instrument,
                granularity
            )
            print(ma_result)
            result_list.append(ma_result)

    process_results(result_list, filepath)


def run_ma_sim(
        curr_list=['CAD', 'JPY', 'NZD', 'GBP'],# curr_list is a list of all our tradable in currencies. In the function, there shall be a combination using the list to generate all our tradable instruments
        granularity=['H1'],# granularityt is the list of granularities of the dataset.
        ma_long=[20,40],# ma_long is the list of the longer ma values to be considered.
        ma_short=[10],#ma_short is the list of shorter ma values to be considered.
        filepath='./data'
):
    '''run_ma_sim takes five arguments, is the most basic funtion that impliments the ma strategy.
     curr_list: is the list of all the tradable instruments in our account.
     granuarity: is the list of granuarities of the different datasets of our tradable instruments.
     ma_long: list of our desired long moving averages.
     ma_short: list of our dersired short moving average
     filepath: path to our dataset.
    '''
    ic.LoadInstruments('./data') #load up the instruments
    for g in granularity:#iterate over the granularity to exhauste the different dataset of each pair
        for p1 in curr_list:
            for p2 in curr_list:
                pair = f'{p1}_{p2}'# combine the different currency pair to make a pair
                if pair in ic.instruments_dict.keys(): # check if the pair is in our tradable instruments
                    # if the pair is in our tradable instrument, we use analyse_pair to analyse the dataset corresponding to the pair
                    analyse_pair(ic.instruments_dict[pair], g, ma_long, ma_short, filepath)
        create_ma_res(g)