#encoding=utf-8
import pandas as pd
import numpy as np
from scipy.stats import norm
import scipy.optimize
import matplotlib.pyplot as plt
import os
import logging

import statistics

'''
Question:
'''

# logging setting
# logging.basicConfig(level=logging.INFO)


def openPosition(open_day, bond, stock, rate, sigma_s):
    ''' 计算开仓数据 '''
    # 开仓时间
    open_t = ((open_day['Date'] - open_day['carrydate']).days + 1) / 365

    # 计算d1
    S = stock[ stock['Date'] == open_day['Date'] ]['close_stock'].iloc[0]  # 开仓当天股票价格
    K = open_day['clause_conversion2_swapshareprice']              # 开仓当天转换价格
    r_rf = rate[rate['Date'] == open_day['Date']]['rate'].iloc[0]          # 无风险利率
    T = bond[bond['Date']==open_day['Date']]['term'].iloc[0]               # 债券到期年限
    sigma_s_od = sigma_s[open_day.name]                         # 开仓日股票波动率

    d1 = ( np.log(S/K) + (r_rf + np.square(sigma_s_od)/2) * (T-open_t) ) \
            / ( sigma_s_od * np.sqrt(T-open_t) )

    # 计算delta 
    delta = np.exp(-1*r_rf * (T-open_t)) * norm.cdf(d1)
    return delta



def calArbitrage(bond_file, stock_file, rate_file, save_file, fig_file,
                 stat_file=None, is_show=False):
    '''计算套利

    Parameters
    ----------
    bond_file : filepath
        可转债文件路径
    stock_file : filepath
        股票文件路径
    rate_file : filepath
        无风险利率文件路径
    save_file: filepath
        套利计算结果保存文件路径
    fig_file: filepath
        套利计算结果图片保存文件路径
    is_show: bool
        True: 显示结果图片
        False: 不显示结果图片
    '''

    # Input File Setting
    #---------------------------------------

    BOND_FILE  = bond_file 
    STOCK_FILE = stock_file
    RATE_FILE  = rate_file 
    SAVE_FILE  = save_file 
    FIG_FILE   = fig_file  


    # Input data
    #---------------------------------------
    logging.info('Loading data...')
    logging.info('bond file: {0}'.format(BOND_FILE))
    logging.info('stock file: {0}'.format(STOCK_FILE))
    logging.info('rate file: {0}'.format(RATE_FILE))

    if os.path.splitext(BOND_FILE)[1] == '.csv':
        # csv file
        with open(BOND_FILE) as fin:  # support for chinese file name
            bond = pd.read_csv(fin, converters={
                'Date':pd.to_datetime, 'ipo_date':pd.to_datetime,
                'carrydate':pd.to_datetime, 'maturitydate':pd.to_datetime})
    else:
        # excel file
        with open(BOND_FILE,'rb') as fin:
            bond = pd.read_excel(fin)

    if os.path.splitext(STOCK_FILE)[1] == '.csv':
        with open(STOCK_FILE) as fin:
            stock = pd.read_csv(fin, converters={'Date':pd.to_datetime})
    else:
        with open(STOCK_FILE,'rb') as fin:
            stock = pd.read_excel(fin)

    if os.path.splitext(RATE_FILE)[1] == '.csv':
        with open(RATE_FILE) as fin:
            rate = pd.read_csv(fin, converters={'Date':pd.to_datetime})
    else:
        with open(RATE_FILE,'rb') as fin:
            rate = pd.read_excel(fin)

    logging.info('Load data complete.')

    # Set valid date time
    # bond = bond[bond['Date']>pd.to_datetime('2018/03/01')].reset_index()

    # Calculate Sigma_s and Sigma_c
    #---------------------------------------
    logging.info('Calculate sigma_s and sigma_c.')
    #FIXME: definition of N and Nd
    # 可转债数据天数Nd
    Nd = bond.shape[0]
    # 交易天数N 
    N = (bond['Date'][len(bond)-1] - bond['Date'][0]).days

    logging.info('可转债交易天数Nd: {0}'.format(Nd))
    logging.info('stock交易的日历天数N: {0}'.format(N))

    # 股票日收益率r
    r = pd.Series(np.nan, index=range(Nd))  # init
    close_stock = stock.loc[:,['Date', 'close_stock']]
    #TODO: using iterators
    for idx in range(Nd):
        if idx:  # skip first day
            tmp1 = close_stock[close_stock['Date']==bond['Date'][idx]
                               ]['close_stock'].iloc[0]
            tmp2 = close_stock[close_stock['Date']==bond['Date'][idx-1]
                               ]['close_stock'].iloc[0]
            r[idx] = tmp1 / tmp2 - 1

    # 计算股票的平均收益率r_mean
    #NOTE: nan will be excluded in  mean()
    r_mean = r.mean()

    logging.info('股票平均收益率r_mean: {0}'.format(r_mean))

    # 计算股票日波动率sigma_s
    lambd = 0.94                       # 衰减因子
    M = 20                             # 迭代天数
    sigma_s = pd.Series(np.nan, index=range(Nd))
    #TODO: using iterators
    for idx in range(M, Nd):       # skip first M days
        suma = 0
        for day in range(1, M+1):
            suma = suma + np.power(lambd,day-1) * np.square(r[idx+1-day] - r_mean)
        sigma_s[idx] = np.sqrt(N * (1-lambd) * suma)

    # 可转债的到期年限T
    T = bond['term'][0]

    # 纯债价格V
    C = 100                                  # 可转债面值
    inter = bond['couponrate'][0]/100        # 可转债利率
    V = 0                                    # 纯债价格
    r_rf = rate['rate'][0]                   # 无风险利率
    for idx in range(1, int(2*T)+1):
        V = V + (C*inter/2) / np.power(1+r_rf/2,idx)
            
    V = V + C / np.power(1+r_rf/2,2*T)

    logging.info('可转债面值C: {0}'.format(C))
    logging.info('可转债年利率i: {0}'.format(inter))
    logging.info('到期年限T: {0}'.format(T))
    logging.info('纯债价格V: {0}'.format(V))

    # 期权价格
    opt_price = pd.Series(np.nan, index=range(Nd))                # 期权价格
    swap_price = bond['close']                                    # 可转债价格
    conversion = bond['clause_conversion2_conversionproportion']  # 转换比例
    for idx in range(Nd):
        opt_price[idx] = (swap_price[idx] - V) / conversion[idx]

    # 计算隐含波动率sigma_c
    # 隐含波动率函数
    def optionPriceFunc(sigma_c, opt_price, S, K, r_rf, T, t_now):
        # 计算d1
        d1 = ( np.log(S/K) + (r_rf + np.square(sigma_c)/2) * (T-t_now) ) \
                / ( sigma_c * np.sqrt(T-t_now) )
        d2 = d1 - sigma_c * np.sqrt(T-t_now)
        return S*norm.cdf(d1) - K*np.exp(-1*r_rf*(T-t_now))*norm.cdf(d2)\
                - opt_price


    # 隐含波动率
    sigma_c = pd.Series(np.nan, index=range(Nd))
    for idx in range(Nd):
        if idx:  # skip first day
            # 当天股票价格
            #FIXME: 先选出该交易日的数据
            # 当天股票价格
            S = stock[stock['Date'] == bond['Date'][idx]]['close_stock'].iloc[0]
            # 当天转换价格
            K = bond['clause_conversion2_swapshareprice'][idx]
            # 无风险利率
            r_rf = rate[rate['Date'] == bond['Date'][idx]]['rate'].iloc[0]          
            # 债券到期年限
            T = bond[bond['Date']==bond['Date'][idx]]['term'].iloc[0]               
            # 当天时间
            t_now = ((bond['Date'][idx] - bond['carrydate'][idx]).days + 1) / 365
            sigma_c[idx] = scipy.optimize.fsolve(optionPriceFunc, 0.4, 
                                args=(opt_price[idx],S,K,r_rf,T,t_now),
                                maxfev=100000000,xtol=1e-19)


    sigma_dif = sigma_s - sigma_c
    logging.info('----------Statistics of sigma_s------------')
    logging.info('Max: {0}, Min: {1}, Mean: {2}'.format(
        sigma_s.max(), sigma_s.min(), sigma_s.mean()) )
    logging.info('----------Statistics of sigma_c------------')
    logging.info('Max: {0}, Min: {1}, Mean: {2}'.format(
        sigma_c.max(), sigma_c.min(), sigma_c.mean()) )
    logging.info('----------Statistics of sigma_s - sigma_c------------')
    logging.info('Max: {0}, Min: {1}, Mean: {2}'.format(
        sigma_dif.max(), sigma_dif.min(), sigma_dif.mean()) )
    del sigma_dif



    # Find arbitrage windows
    #----------------------------------------
    logging.info('Finding arbitrage windows...')
    phi1 = 0.2
    phi2 = 0
    # 开仓条件
    open_pos = ((sigma_s - sigma_c) >= phi1)
    # 平仓条件
    close_pos = ((sigma_s - sigma_c) <= phi2)
    # close position should be after open position
    if close_pos[open_pos].size:  # open position not none
        close_pos[0:close_pos[open_pos].index[0]] = False

    # arbitrage result
    result = pd.DataFrame(columns=['open','close','days','profit'])
    count = 0
    delta_sum = 0
    while True in open_pos.unique():
        ''' loop until no more open position left '''

        count = count + 1

        # 开仓当天数据
        open_day = bond[open_pos].iloc[0]
        if not bond[close_pos].size:  
            # 所有交易日结束也没满足平仓条件
            # 将平仓日期设为最后一个交易日
            close_day = bond.iloc[len(bond)-1]
        else: 
            close_day = bond[close_pos].iloc[0]
        logging.info('----------No.{0} arbitrage window----------'.format(count))
        logging.info('Open day: {0}'.format(open_day['Date']))
        logging.info('Close day: {0}'.format(close_day['Date']))

        # update next position
        open_pos[open_day.name:close_day.name+1] = False
        if close_pos[open_pos].size:
            # still have open position, if not the loop will exit
            close_pos[close_day.name:close_pos[open_pos].index[0]] = False

        # 套利持续天数t_alpha
        t_alpha = (close_day['Date'] - open_day['Date']).days + 1
        logging.info('Arbitrage window size: {0}'.format(t_alpha))

        # 计算delta
        delta = openPosition(open_day, bond, stock, rate, sigma_s)
        delta_sum = delta_sum + delta
        logging.info('delta: {0}'.format(delta))

        # 套期收益R
        CB_T = close_day['close']  # 可转债平仓日价格
        CB_t = open_day['close']   # 可转债开仓日价格
        # 平仓日可转债对应股票价格
        S_T = stock[stock['Date'] == close_day['Date']]['close_stock'].iloc[0]
        # 开仓日可转债对应股票价格
        S_t = stock[stock['Date'] == open_day['Date']]['close_stock'].iloc[0]
        R = (CB_T - CB_t) - delta*(S_T - S_t)
        logging.info('Arbitrage profit: {0}'.format(R))

        # store result
        res_dict = {'open':open_day['Date'], 'close':close_day['Date'],
                    'days':t_alpha, 'profit':R, 'delta':delta}
        result = result.append(res_dict, ignore_index=True)
    
    if count:
        delta_mean = delta_sum / count
    else:
        delta_mean = np.nan
    logging.info('Mean of delta: {0}'.format(delta_mean))


    # Output
    #----------------------------------------
    # output result in to file
    result.to_csv(SAVE_FILE, index=False)

    arbi = statistics.loadResult(SAVE_FILE)
    # 年化收益率，年化波动率，夏普比率
    ar, asigma_g, sharpe, max_drawdown = statistics.calStatistics(bond,rate,arbi)
    stat_data = {'delta_mean':delta_mean,'ar':ar, 'asigma_g':asigma_g,
                 'sharpe':sharpe, 'max_drawdown':max_drawdown}
    if stat_file:
        stat = pd.DataFrame(columns=['delta_mean','ar', 'asigma_g',
                                     'sharpe','max_drawdown'])
        stat = stat.append(stat_data, ignore_index=True)
        stat.to_csv(stat_file, index=False)
    # plot result
    plt.clf()
    plt.plot(bond['Date'], sigma_s, bond['Date'], sigma_c,
            bond['Date'], sigma_s-sigma_c)
    plt.legend(['Sigma_s', 'Sigma_c', 'Sigma_s - Sigma_c'])
    # save plot to file
    plt.savefig(FIG_FILE, dpi=400)
    # show the plot
    if is_show:
        plt.show()

    return stat_data


def test_calArbitrage_excel():
    BOND_FILE = 'bond.xlsx'
    STOCK_FILE = 'stock.xlsx'
    RATE_FILE = 'rate.xlsx'
    SAVE_FILE = 'result.csv'
    FIG_FILE = 'result.png'
    calArbitrage(BOND_FILE,STOCK_FILE,RATE_FILE,SAVE_FILE,FIG_FILE)


def test_calArbitrage_csv():
    BOND_FILE = 'bond.csv'
    STOCK_FILE = 'stock.csv'
    RATE_FILE = 'rate.xlsx'
    SAVE_FILE = 'result.csv'
    FIG_FILE = 'result.png'
    calArbitrage(BOND_FILE,STOCK_FILE,RATE_FILE,SAVE_FILE,FIG_FILE)
    
def test_1():
    BOND_FILE = './test/statistics/民生/bond.xlsx'
    STOCK_FILE = './split_stock/600016.SH/stock.csv'
    RATE_FILE = 'rate.xlsx'
    SAVE_FILE = './test/statistics/民生/result.csv'
    FIG_FILE = './test/statistics/民生/result.png'
    STAT_FILE = './test/statistics/民生/statistics.csv'
    calArbitrage(BOND_FILE,STOCK_FILE,RATE_FILE,SAVE_FILE,FIG_FILE,STAT_FILE,is_show=False)



if __name__ == '__main__':
    test_1()
