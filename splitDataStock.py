import csv
import os
import time

# 股票文件
#NOTE: 删除了源文件中的公司名称、中文列名
#      包含股票代码、英文列名和数据
STOCK_FILE = 'data_stock.csv'
# 分离后的数据保存目录
SPLIT_DIR = './split_stock'
# 一个公司数据对应的列数
NCOL = 8


start_time = time.time()

with open(STOCK_FILE) as stock:
    reader = csv.reader(stock)
    # get header, first row
    company = reader.__next__()
    company = list(filter(None,company))  # remove null
    count = 1
    for row in reader:
        print('Processing row: {0}'.format(count))
        count = count + 1
        # 可转债数量
        Nfile = (len(row)+1) // NCOL
        for idx in range(Nfile):
            save_dir = os.path.join(SPLIT_DIR,company[idx])
            try:
                os.mkdir(save_dir)
            except:
                pass
            with open(os.path.join(save_dir,'stock.csv'), 'a') as out:
                writer = csv.writer(out)
                writer.writerow(row[0+idx*NCOL:NCOL-1+idx*NCOL])

print('Time use: {0}'.format(time.time()-start_time))
