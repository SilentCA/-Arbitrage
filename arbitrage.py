#encoding=utf-8
import pandas as pd
import numpy as np

BOND_FILE = 'bond.xlsx'
STOCK_FILE = 'stock.xlsx'
RATE_FILE = 'rate.xlsx'

# Input data
#---------------------------------------
bond = pd.read_excel(BOND_FILE)
stock = pd.read_excel(STOCK_FILE)

# Calculate Sigma_s and Sigma_c
#---------------------------------------
# 交易天数N 
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
lambda = 0.94
M = 20
sigma_s = pd.Series(np.nan, index=range(N))
#TODO: using iterators
for idx in range(N):
    sum = 0
    for day in range(1, M+1):
        sum = sum + np.power(lambda,day-1) * (r[idx+1-day] - r_mean)
    sigma_s(idx) = np.sqrt(N * (1-lambda) * sum)

#FIXME: Question
# 可转债的到期年限T
T = bond['maturitydate'][-1] - bond['ipo_date'][0]

# 纯债价格V
#TODO: correct the values below
C = 1                # 可转债面值
inter = 1            # 可转债利率
V = 0
for idx in range(1, T.days+1):
    V = V + (C*inter/2) / np.power(1+inter/2,idx) +
        C / np.power(1+inter/2,2*T)

# 期权价格



# Find arbitrage windows
#----------------------------------------


# Output
#----------------------------------------
