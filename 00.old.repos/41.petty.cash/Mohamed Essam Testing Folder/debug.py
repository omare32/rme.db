import pandas as pd

df = pd.read_excel('PK101 2019 log.xlsx', sheet_name='78')
df.columns = df.loc[4]
df = df[6:]

keep = []
for index, value in df.iloc[:,1].iteritems():
    if value is None:
        break
    else:
        keep.append(index)