#encoding=utf-8
import pandas as pd
import numpy as np
import os
import logging


# logging setting
logging.basicConfig(level=logging.INFO)


# Input File Setting
#---------------------------------------
BOND_FILE  = './test/statistics/bond.csv'
RATE_FILE  = 'rate.xlsx'
ARBITRAGE_RESULT_FILE = './test/statistics/result.csv'


# Input data
#---------------------------------------
logging.info('Loading data...')
logging.info('bond file: {0}'.format(BOND_FILE))
logging.info('rate file: {0}'.format(RATE_FILE))

# load bond
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

# load rate
if os.path.splitext(RATE_FILE)[1] == '.csv':
    with open(RATE_FILE) as fin:
        rate = pd.read_csv(fin, converters={'Date':pd.to_datetime})
else:
    with open(RATE_FILE,'rb') as fin:
        rate = pd.read_excel(fin)

# load result from arbitrage computation
with open(ARBITRAGE_RESULT_FILE) as fin:
    arbi = pd.read_csv(fin, converters={'open':pd.to_datetime, 
                                'close':pd.to_datetime})

logging.info('Load data complete.')


# 转债净值NV
#---------------------------------------
NV = bond.loc[:, ['Date', 'close']].copy()
for idx in range(len(arbi)):
    NV[ NV['Date']>=arbi['open'][idx] ]['close'] =\
                    NV[ NV['Date']>=arbi['open'][idx] ]['close'] +\
                    arbi['profit'][idx]

# 转债净增长率
g = pd.Series(np.nan, index=range(len(NV)))
for idx in range(len(NV)):
    if idx:  # skip first day
        g[idx] = NV[idx] / NV[idx-1] - 1

# 转债净值日增长率均值
g_mean = g.mean()
logging.info('净值增长率均值：{0}'.format(g_mean))

# 转债净值增长率波动率
sigma_g = g.var()  # default normalized by N-1
logging.info('净值增长率波动率：{0}'.format(sigma_g))

# 转债年化收益率
# skip first day: g(1:)
ar = np.power(np.prod(g[1:]+1), (len(g)-1)/365)
logging.info('年化收益率：{0}'.format(ar))

# 转债年化波动率
asigma_g = np.sqrt(365) * sigma_g
logging.info('年化波动率：{0}'.format(asigma_g))

# 无风险收益率均值
r_rf_sum = 0
for idx in range(len(NV)):
    r_rf_sum = rate[ rate['Date']==NV['Date'][idx] ]['rate'].iloc[0]
r_rf_mean = r_rf_sum / len(NV)
logging.info('无风险收益率均值：{0}'.format(rf_mean))

# 夏普比率
sharpe = (g_mean - r_rf_mean) / sigma_g
logging.info('夏普比率：{0}'.format(sharpe))

# output = pd.DataFrame(columns=[''])
