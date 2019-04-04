import os
import pandas as pd
import logging
import arbitrage


logging.basicConfig(level=logging.INFO,
                   filename='arbitrage.log',
                   filemode='a')

# Path Setting
#-------------------------------
# bond数据文件目录
BOND_DIR = './data/Bond_filter/Bond_filter'
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


# BOND_DIR中的所有bond
_, bond_paths, _ = os.walk(BOND_DIR).__next__()
bond_paths.sort()


# 计算所有的可转债
fail_list = []
for idx, bond_path in enumerate(bond_paths):
    idx = idx + 1
    if idx <= 146:
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

    logging.info('stock file: {0}'.format(stock_file))
    logging.info('rate file: {0}'.format(rate_file))

    arbitrage.calArbitrage(bond_file,stock_file,rate_file,
                save_file,fig_file)
    # 计算套利
    try:
        arbitrage.calArbitrage(bond_file,stock_file,rate_file,
                    save_file,fig_file)
    except:
        logging.info('Computing failure: {0}\n{1}'.format(bond_path,e))
        fail_list.append(bond_path)

logging.info('Failure when computing:')
logging.info('\n'.join(fail_list))
