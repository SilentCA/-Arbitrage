#encoding=utf-8
import pandas as pd
import numpy as np
from scipy.stats import norm
import matplotlib.pyplot as plt
import logging

'''
Question:
'''

# logging setting
logging.basicConfig(level=logging.INFO)

BOND_FILE = 'bond.xlsx'
STOCK_FILE = 'stock.xlsx'
RATE_FILE = 'rate.xlsx'
SAVE_FILE = 'result.csv'
FIG_FILE = 'result.png'

# Input data
#---------------------------------------
logging.info('Loading data...')
bond = pd.read_excel(BOND_FILE)
stock = pd.read_excel(STOCK_FILE)
rate = pd.read_excel(RATE_FILE)
logging.info('Load data complete.')

# Calculate Sigma_s and Sigma_c
#---------------------------------------
logging.info('Calculate sigma_s and sigma_c.')
#FIXME: definition of N and Nd
# 可转债数据天数Nd
Nd = bond.shape[0]
# 交易天数N 
N = (stock['Date'][len(stock)-1] - stock['Date'][0]).days

# 股票日收益率r
r = pd.Series(np.nan, index=range(Nd))  # init
close_stock = stock['close_stock']
#TODO: using iterators
for idx in range(Nd):
    if idx:  # skip first day
        r[idx] = close_stock[idx] / close_stock[idx-1] - 1

# 计算股票的平均收益率r_mean
#NOTE: nan will be excluded in  mean()
r_mean = r.mean()

# 计算股票日波动率sigma_s
lambd = 0.94                       # 衰减因子
M = 20                             # 迭代天数
sigma_s = pd.Series(np.nan, index=range(Nd))
#TODO: using iterators
for idx in range(M, Nd):       # skip first M days
    sum = 0
    for day in range(1, M+1):
        sum = sum + np.power(lambd,day-1) * np.square(r[idx+1-day] - r_mean)
    sigma_s[idx] = np.sqrt(N * (1-lambd) * sum)

# 可转债的到期年限T
T = bond['term'][0]

# 纯债价格V
C = 100                                  # 可转债面值
inter = bond['couponrate'][0] / 100      # 可转债利率
V = 0                                    # 纯债价格
for idx in range(1, 2*T+1):
    V = V + (C*inter/2) / np.power(1+inter/2,idx) + \
        C / np.power(1+inter/2,2*T)

# 期权价格
opt_price = pd.Series(np.nan, index=range(Nd))                # 期权价格
swap_price = bond['close']                                    # 可转债价格
conversion = bond['clause_conversion2_conversionproportion']  # 转换比例
for idx in range(Nd):
    opt_price[idx] = (swap_price[idx] - V) / conversion[idx]

# 可转债的隐含波动率sigma_c，即期权价格的波动率
# 期权价格日收益率ro
ro = pd.Series(np.nan, index=range(Nd))  # init
#TODO: using iterators
for idx in range(Nd):
    if idx:  # skip first day
        ro[idx] = opt_price[idx] / opt_price[idx-1] - 1

# 计算期权价格的平均收益率ro_mean
#NOTE: nan will be excluded in  mean()
ro_mean = ro.mean()

# 计算隐含波动率sigma_c
lambd = 0.94
M = 20
sigma_c = pd.Series(np.nan, index=range(Nd))
#TODO: using iterators
for idx in range(M,Nd):  # skip first M days
    sum = 0
    for day in range(1, M+1):
        sum = sum + np.power(lambd,day-1) * np.square(ro[idx+1-day] - ro_mean)
    sigma_c[idx] = np.sqrt(Nd * (1-lambd) * sum)

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
def openPosition(open_day, bond, stock, rate):
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
    delta = np.exp(-1*r_rf * (T-open_t)) * norm.pdf(d1)
    return delta


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

result = pd.DataFrame(columns=['open','close','days','profit'])
count = 1
while True in open_pos.unique():
    ''' loop until no more open position left '''

    # 开仓当天数据
    open_day = bond[open_pos].iloc[0]
    if not bond[close_pos].size:  
        # 所有交易日结束也没满足平仓条件
        # 将平仓日期设为最后一个交易日
        close_day = bond.iloc[len(bond)-1]
    else: 
        close_day = bond[close_pos].iloc[0]
    logging.info('----------No.{0} arbitrage window----------'.format(count))
    count = count + 1
    logging.info('Open day: {0}'.format(open_day['Date']))
    logging.info('Close day: {0}'.format(close_day['Date']))

    # update next position
    open_pos[open_day.name:close_day.name+1] = False
    if close_pos[open_pos].size:
        # still have open position, if not the loop will exit
        close_pos[close_day.name:close_pos[open_pos].index[0]] = False


    # 计算delta
    delta = openPosition(open_day, bond, stock, rate)

    # 套利持续天数t_alpha
    t_alpha = (close_day['Date'] - open_day['Date']).days + 1
    logging.info('Arbitrage window size: {0}'.format(t_alpha))

    # 套期收益R
    CB_T = close_day['close']  # 可转债平仓日价格
    CB_t = open_day['close']   # 可转债开仓日价格
    # 平仓日可转债对应股票价格
    S_T = stock[stock['Date'] == close_day['Date']]['close_stock'].iloc[0]
    # 开仓日可转债对应股票价格
    S_t = stock[stock['Date'] == open_day['Date']]['close_stock'].iloc[0]
    R = (CB_T - CB_t) - delta*(S_T - S_t)
    logging.info('Arbitrage profit: {0}'.format(R))

    res_dict = {'open':open_day['Date'], 'close':close_day['Date'],
                   'days':t_alpha, 'profit':R}
    result = result.append(res_dict, ignore_index=True)




# Output
#----------------------------------------
# output result in to file
result.to_csv(SAVE_FILE)
# plot result
plt.plot(bond['Date'], sigma_s, bond['Date'], sigma_c,
        bond['Date'], sigma_s-sigma_c)
plt.legend(['Sigma_s', 'Sigma_c', 'Sigma_s - Sigma_c'])
# save plot to file
plt.savefig(FIG_FILE)
# show the plot
plt.show()
