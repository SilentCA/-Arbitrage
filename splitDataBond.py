import csv
import os
import time

# 可转债文件
#NOTE: 删除了源文件中的公司名称、中文列名
#      仅包含英文列名和数据
BOND_FILE = 'data_bond_test.csv'
# 分离后的数据保存目录
SPLIT_DIR = './split'


start_time = time.time()

with open(BOND_FILE) as bond:
    reader = csv.reader(bond)
    # get header, first row
    company = reader.__next__()
    company = list(filter(None,company))  # remove null
    # skip second and third rows
    reader.__next__()
    reader.__next__()
    count = 1
    for row in reader:
        print('Processing row: {0}'.format(count))
        count = count + 1
        # 可转债数量
        Nfile = (len(row)+1) // 12
        for idx in range(Nfile):
            save_dir = os.path.join(SPLIT_DIR,company[idx])
            try:
                os.mkdir(save_dir)
            except:
                pass
            with open(os.path.join(save_dir,'bond.csv'), 'a') as out:
                writer = csv.writer(out)
                writer.writerow(row[0+idx*12:11+idx*12])

print('Time use: {0}'.format(time.time()-start_time))
