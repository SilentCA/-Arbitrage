#encoding=utf-8
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import logging


# logging setting
# logging.basicConfig(level=logging.INFO)


def loadData(bond_file, rate_file):
    # Input data
    #---------------------------------------
    logging.info('Loading data...')
    logging.info('bond file: {0}'.format(bond_file))
    logging.info('rate file: {0}'.format(rate_file))

    # load bond
    if os.path.splitext(bond_file)[1] == '.csv':
        # csv file
        with open(bond_file) as fin:  # support for chinese file name
            bond = pd.read_csv(fin, converters={
                'Date':pd.to_datetime, 'ipo_date':pd.to_datetime,
                'carrydate':pd.to_datetime, 'maturitydate':pd.to_datetime})
    else:
        # excel file
        with open(bond_file,'rb') as fin:
            bond = pd.read_excel(fin)

    # load rate
    if os.path.splitext(rate_file)[1] == '.csv':
        with open(rate_file) as fin:
            rate = pd.read_csv(fin, converters={'Date':pd.to_datetime})
    else:
        with open(rate_file,'rb') as fin:
            rate = pd.read_excel(fin)

    return (bond, rate)


def loadResult(filename):
    # load result from arbitrage computation
    with open(filename) as fin:
        arbi = pd.read_csv(fin, converters={'open':pd.to_datetime, 
                                    'close':pd.to_datetime})
    return arbi


def maxDrawdown(return_list):
    '''最大回撤率'''
    i = np.argmax((np.maximum.accumulate(return_list) - return_list) / np.maximum.accumulate(return_list))  # 结束位置
    if i == 0:
        return 0, 0, 0
    j = np.argmax(return_list[:i])  # 开始位置
    return (return_list[j] - return_list[i]) / (return_list[j]), j, i


def calStatistics(bond, rate, arbi, isPlot=False):
    # 可转债净值NV
    #---------------------------------------
    # NV = bond.loc[:, ['Date', 'close']].copy()
    NV = pd.DataFrame(bond.loc[:, ['Date', 'close']])
    for idx in range(len(arbi)):
        NV.loc[ NV['Date']>=arbi['open'][idx], 'close' ] =\
                        NV[ NV['Date']>=arbi['open'][idx] ]['close'] +\
                        arbi['profit'][idx]

    if isPlot:
        plt.clf()
        plt.plot(NV['close'])
        plt.show()

    # 可转债净增长率
    g = pd.Series(np.nan, index=range(len(NV)))
    for idx in range(len(NV)):
        if idx:  # skip first day
            g[idx] = NV['close'][idx] / NV['close'][idx-1] - 1

    # 可转债净值日增长率均值
    g_mean = g.mean()
    logging.info('净值增长率均值：{0}'.format(g_mean))

    # 转债净值增长率波动率
    sigma_g = g.std()  # default normalized by N-1
    logging.info('净值增长率波动率：{0}'.format(sigma_g))

    # 可转债年化收益率
    # skip first day: g[1:]
    ar = np.power(np.prod(g[1:]+1), 252/(len(g)-1)) - 1
    logging.info('年化收益率：{0}'.format(ar))

    # 可转债年化波动率
    asigma_g = np.sqrt(252) * sigma_g
    logging.info('年化波动率：{0}'.format(asigma_g))

    # 无风险收益率均值
    r_rf_sum = 0
    for idx in range(len(NV)):
        r_rf_sum = r_rf_sum + rate[ rate['Date']==NV['Date'][idx] ]['rate'].iloc[0]
    r_rf_mean = r_rf_sum / len(NV)
    logging.info('无风险收益率均值：{0}'.format(r_rf_mean))

    # 夏普比率
    # sharpe = ( g_mean - (np.power(1+r_rf_mean,1/365) - 1) ) / sigma_g
    sharpe = (ar-r_rf_mean) / asigma_g
    logging.info('夏普比率：{0}'.format(sharpe))

    # 最大回撤率
    max_drawdown, mdd_start, mdd_end = maxDrawdown(NV['close'])
    logging.info('最大回撤率: {0}，start: {1}, end: {2}'.format(
                    max_drawdown, mdd_start, mdd_end))

    return ar, asigma_g, sharpe, max_drawdown

def test_statistics():
    # Input File Setting
    #---------------------------------------
    BOND_FILE  = './test/statistics/民生/bond.xlsx'
    RATE_FILE  = 'rate.xlsx'
    ARBITRAGE_RESULT_FILE = './test/statistics/民生/result.csv'

    (bond, rate) = loadData(BOND_FILE, RATE_FILE)
    arbi = loadResult(ARBITRAGE_RESULT_FILE)
    logging.info('Load data complete.')
    
    ar, asigma_g, sharpe, max_drawdown = calStatistics(bond,rate,arbi,isPlot=True)


if __name__ == "__main__":
    test_statistics()
