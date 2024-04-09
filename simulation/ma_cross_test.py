import pandas as pd
from infrastructure.instrument_collection import instrumentCollection as ic

BUY = 1
SELL = -1
NONE = 0

get_ma_col = lambda x: f'MA_{x}'

def load_price_data(pair, granularity, ma_list):
    # this function loads the dataset and creates ma columns from the ma_list given to it
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

def get_trades(df_analysis, instrument):
    # get_tarde uses the instrument.pipLocation to calculate the pips lost or gained by the ma crossover
    df_trades = df_analysis[df_analysis['Trades']!=NONE].copy()
    df_trades['Diff'] = df_trades['mid_c'].diff().shift(-1)
    df_trades.fillna(0, inplace=True)
    df_trades['Gain'] = df_trades['Diff'] / instrument.pipLocation
    df_trades['Gain'] = df_trades['Gain'] * df_trades['Trades']
    total_gain = df_trades['Gain'].sum()
    return dict(total_gain=int(total_gain), df_trades=df_trades)

def assess_pair(price_data, ma_l, ma_s, instrument):
    #assess_pair performs relevant data prepatations in order to assess the performance of the startegy
    #it uses the get_trade to complete this task
    df_analysis = price_data.copy()
    df_analysis['Delta'] = df_analysis[ma_s] - df_analysis[ma_l]
    df_analysis['Delta_Prev'] = df_analysis['Delta'].shift(1)
    df_analysis['Trades'] = df_analysis.apply(is_trade, axis=1)
    # print(ma_l,ma_s)
    # print(df_analysis.head(3))
    return get_trades(df_analysis, instrument)

# analyse _pair is the function that will be fed into run_ma_sim. the function will take an instrument, the granukarity in or oder to read the 
# dataset that corresponds to the pair and granularity. It takes the lists of the ma_long and ma_short and combine them.
def analyse_pair(instrument, granularity, ma_long, ma_short):
    ma_list = set(ma_long + ma_short)
    pair = instrument.name

    #the ma_list is fed into load_price_data where the dataset is finally read in having the columns of all the MAs
    price_data = load_price_data(pair, granularity, ma_list)

    # print(pair)
    # print(price_data.head(3))
    # the ma_long and ma_short values are interated over and each combinations is fed into assess_pair
    # assess_pair creates a column for each ma in the into the dataset and performs other data preparations necessary
    for ma_l in ma_long:
        for ma_s in ma_list:
            if ma_l <= ma_s:
                continue
            result = assess_pair(
                price_data,
                get_ma_col(ma_l),
                get_ma_col(ma_s),
                instrument
            )
            tg = result['total_gain']
            nt = result['df_trades'].shape[0]

            print(f'{pair} {granularity} {ma_s}-{ma_l} nt:{nt} tg:{tg}')

# run_ma_sim is the main function to impliment the ma crossover startegy for all the pairs provided
def run_ma_sim(
        curr_list=['EUR', 'USD'],# curr_list is a list of all our tradable in currencies. In the function, there shall be a combination using the list to generate all our tradable instruments
        granularity=['H1'],# granularityt is the list of granularities of the dataset.
        ma_long=[20,40,80],# ma_long is the list of the longer ma values to be considered.
        ma_short=[10,20]#ma_short is the list of shorter ma values to be considered.
):
    ic.LoadInstruments('./data')#load up the instruments
    for g in granularity:#iterate over the granularity to exhauste the different dataset of each pair
        for p1 in curr_list:
            for p2 in curr_list:
                pair = f'{p1}_{p2}'# combine the different currency pair to make a pair
                if pair in ic.instruments_dict.keys(): # check if the pair is in our tradable instruments
                    analyse_pair(ic.instruments_dict[pair], g, ma_long, ma_short)
    