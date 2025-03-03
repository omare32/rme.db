import csv

header=['name', 'ar', 'en', 'math']

with open('details2.csv','a',newline='') as f:
    w=csv.writer(f)
    while True:
        opt=int(input('enter ur option no \n 1-add \n 2-exit \n'))
        if opt==2:
            break
        row=[input('enter ur name: ')]
        row.extend([int(input(f'Enter {header[sub]} grade: ')) for sub in range(1,len(header))])
        w.writerow(row)