import pandas as pd
df=pd.read_csv('RME_Material_Movement_with_cos_090623.csv',encoding='utf-8-sig')
df = df[df['Item Desc'].str.contains('حديد تسليح')==True]
df.to_excel("RME_Material_Movement_with_cos_090623.new.xlsx")