# bond数据分离spliData.py
- 修改程序中`BOND_FILE`为需要分离的bond数据文件路径
- 修改程序中`SPLIT_DIR`为分离的数据保存路径
- 分离之后的数据保存在`SPLIT_DIR`中，每一个可转债的
数据存放在不同的子目录中的`bond.csv`文件中。

## Note
- 需要将bond的原始文件中的前面三行删掉，只留下来英文的列名和数据
原始文件如下
![](./pic/data_bond_origin.PNG)
修改之后如下
![](./pic/data_bond_modify.PNG)
