#encoding=utf-8
import pandas as pd
import numpy as np
from scipy.stats import norm
import logging

'''
Question:
    - 可转债
'''

# logging setting
logging.basicConfig(level=logging.INFO)

BOND_FILE = 'bond.xlsx'
STOCK_FILE = 'stock.xlsx'
RATE_FILE = 'rate.xlsx'

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
# 交易天数N 
#FIXME: definition of N
N = len(bond['Date'])

# 股票日收益率r
r = pd.Series(np.nan, index=range(N))  # init
close_stock = stock['close_stock']
#TODO: using iterators
for idx in range(N):
    if idx:  # skip first day
        r[idx] = close_stock[idx] / close_stock[idx-1]

# 计算股票的平均收益率r_mean
#FIXME: how to handle nan in mean()
r_mean = r.mean()

# 计算股票日波动率sigma_s
lambd = 0.94
M = 20
sigma_s = pd.Series(np.nan, index=range(N))
#TODO: using iterators
#FIXME: 前面20天的如何计算
for idx in range(20,N):
    sum = 0
    for day in range(1, M+1):
        sum = sum + np.power(lambd,day-1) * np.square(r[idx+1-day] - r_mean)
    sigma_s[idx] = np.sqrt(N * (1-lambd) * sum)

# 可转债的到期年限T
T = (bond['maturitydate'][N-1] - bond['ipo_date'][0]).days + 1

# 纯债价格V
C = 100                            # 可转债面值
inter = bond['couponrate'][0]      # 可转债利率
V = 0                              # 纯债价格
#FIXME: T is very large causing overflow, check T's definition
for idx in range(1, T+1):
    V = V + (C*inter/2) / np.power(1+inter/2,idx) + \
        C / np.power(1+inter/2,2*T)

# 期权价格
#FIXME: 可转债价格和转股价格
opt_price = pd.Series(np.nan, index=range(N))  # 期权价格
swap_price = bond['clause_conversion2_swapshareprice']        # 转股价格
conversion = bond['clause_conversion2_conversionproportion']  # 转换比例
for idx in range(N):
    opt_price[idx] = (swap_price[idx] - V) / conversion[idx]

# 可转债的隐含波动率sigma_c，即期权价格的波动率
# 期权价格日收益率ro
ro = pd.Series(np.nan, index=range(N))  # init
#TODO: using iterators
for idx in range(N):
    if idx:  # skip first day
        ro[idx] = opt_price[idx] / opt_price[idx-1]

# 计算期权价格的平均收益率ro_mean
#FIXME: how to handle nan in mean()
ro_mean = ro.mean()

# 计算隐含波动率sigma_c
lambd = 0.94
M = 20
sigma_c = pd.Series(np.nan, index=range(N))
#TODO: using iterators
#FIXME: 前面20天的如何计算
for idx in range(20,N):  # skip first 20 days
    sum = 0
    for day in range(1, M+1):
        sum = sum + np.power(lambd,day-1) * np.square(ro[idx+1-day] - ro_mean)
    sigma_c[idx] = np.sqrt(N * (1-lambd) * sum)


#TODO: use function
# Find arbitrage windows
#----------------------------------------
phi1 = 0.2
phi2 = 0
# 开仓条件
open_pos = ((sigma_s - sigma_c) >= phi1)
# 平仓条件
close_pos = ((sigma_s - sigma_c) <= phi2)
# 开仓时间
#FIXME: 开仓时间
opent_t = 1

# 计算d1
open_day = bond[open_pos].iloc[0]   # 开仓当天数据
#FIXME: S， r_rf
#FIXME: index by Date
S = stock[open_day['Date'],'close_stock']       # 开仓当天股票价格
K = open_day['clause_conversion2_swapshareprice']  # 开仓当天转换价格
r_rf = rate[open_day['Date'], 'rate']
sigma_s_od = sigma_s[open_pos].iloc[0]    # 开仓日股票波动率
d1 = ( np.log(S/K) + (r_rf + np.square(sigma_s_od)/2) * (T-open_t) ) \
        / ( sigma_s_od * np.square(T-t) )

# 计算delta 
delta = np.exp(-1*r_rf * (T-open_t)) * norm.pdf(d1)

#TODO
# 开仓操作


# Output
#----------------------------------------
