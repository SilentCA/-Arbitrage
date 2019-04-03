import os
import csv
import logging


# logging setting
#-------------------------------
logging.basicConfig(level=logging.INFO)


# Path Setting
#-------------------------------
# bond数据文件目录
BOND_DIR = './split_bond'


# BOND_DIR中的所有bond
_, bond_paths, _ = os.walk(BOND_DIR).__next__()

# 计算所有的可转债
for idx, bond_path in enumerate(bond_paths):
    idx = idx + 1

    logging.info('Filtering No.{0}, bond: {1}'.format(idx,bond_path))

    bond_file = os.path.join(BOND_DIR,bond_path,'bond.csv')
    with open(bond_file) as fin:
        reader = csv.DictReader(fin)
        bond_file_new = os.path.join(BOND_DIR,bond_path,'bond_new.csv')
        with open(bond_file_new, 'a') as fout: 
            writer = csv.DictWriter(fout, reader.fieldnames)
            writer.writeheader()
            # write header
            # writer.writerow(reader.__next__())
            for row in reader:
                isValid = bool(row['clause_conversion2_conversionproportion'])
                isValid = isValid & bool(row['clause_conversion2_swapshareprice'])
                isValid = isValid & bool(row['close'])
                if isValid:
                    writer.writerow(row)
