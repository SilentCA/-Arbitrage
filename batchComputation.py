import os
import pandas as pd
import logging
import matplotlib.pyplot as plt

import arbitrage


logging.basicConfig(level=logging.INFO,
                   filename='arbitrage.log',
                   filemode='a')

# skip first number
SKIP_NUM = 0

# Path Setting
#-------------------------------
# bond数据文件目录
BOND_DIR = './data/Index'
# bond数据文件名
BOND_BASENAME = 'bond_filter_1.csv'
# stock数据文件目录
STOCK_DIR = './split_stock'
# stock数据文件名
STOCK_BASENAME = 'stock.csv'
# 无风险利率文件
RATE_FILE = './rate.xlsx'
# 保存结果文件名
SAVE_FILENAME = 'result.csv'
# 结果图片文件名
FIG_FILENAME = 'result.png'
# 统计数据文件名
STAT_FILENAME = 'statistics.csv'
# 总的统计数据文件名
TOTAL_STAT_FILENAME = 'total_statistics.csv'


# BOND_DIR中的所有bond
_, bond_paths, _ = os.walk(BOND_DIR).__next__()
bond_paths.sort()


# 计算所有的可转债
sigma_c_table = pd.DataFrame()
sigma_s_table = pd.DataFrame()
stat = pd.DataFrame(columns=['bond','delta_mean','ar', 'asigma_g', 'sharpe'])
fail_list = []
for idx, bond_path in enumerate(bond_paths):
    idx = idx + 1
    if idx <= SKIP_NUM:
        continue

    logging.info('computing no.{0}, bond: {1}'.format(idx,bond_path))
    print('computing no.{0}, bond: {1}'.format(idx,bond_path))

    # 找到bond对应的stock
    bond_file = os.path.join(BOND_DIR,bond_path,BOND_BASENAME)
    with open(bond_file) as fin:
        stock_path = pd.read_csv(fin)['underlyingcode'][0]
    stock_file = os.path.join(STOCK_DIR,stock_path,STOCK_BASENAME)
    rate_file = RATE_FILE
    save_file = os.path.join(BOND_DIR,bond_path,SAVE_FILENAME)
    fig_file = os.path.join(BOND_DIR,bond_path,FIG_FILENAME)
    if STAT_FILENAME:
        stat_file = os.path.join(BOND_DIR,bond_path,STAT_FILENAME)

    logging.info('stock file: {0}'.format(stock_file))
    logging.info('rate file: {0}'.format(rate_file))

    # 计算套利
    stat_data = None
    try:
        stat_data, sigma_c, sigma_s = arbitrage.calArbitrage(
                    bond_file,stock_file,rate_file,
                    save_file,fig_file,stat_file,
                    lday=pd.to_datetime('2015/03/01'),
                    rday=pd.to_datetime('2019/03/29'),
                    phi2=-0.1)

        stat_data['bond'] = bond_path
        stat = stat.append(stat_data, ignore_index=True)
        
        sigma_s.name = idx
        sigma_c.name = idx
        sigma_s_table = sigma_s_table.join(sigma_s, how='outer')
        sigma_c_table = sigma_c_table.join(sigma_c, how='outer')
    except:
        logging.info('Computing failure: {0}'.format(bond_path))
        fail_list.append(bond_path)


    
stat.to_csv(os.path.join(BOND_DIR,TOTAL_STAT_FILENAME),index=False)
sigma_s_mean = sigma_s_table.mean(axis=1)
sigma_c_mean = sigma_c_table.mean(axis=1)
plt.clf()
sigma_s_mean.plot()
sigma_c_mean.plot()
(sigma_s_mean - sigma_c_mean).plot()
plt.legend(['Sigma_s', 'Sigma_c', 'Sigma_s - Sigma_c'])
plt.show()



logging.info('Failure when computing:')
logging.info('\n'.join(fail_list))
