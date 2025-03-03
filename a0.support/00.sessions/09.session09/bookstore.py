import pandas as pd

df=pd.read_csv('book_store.csv')

while True:
    option=input('Enter (1)-Admin / (2)-User / (3)-Exit : ')
    if option =='1':
        if input('username: ')=='AdminBS1' and input('Password: ')=='123BS0':
            while True:
                opt=int(input(f'choose an option: \n\t 1-get all the data\n\t 2-add book\n\t 3-delete book\n\t 4-get the book names\n\t 5-get the statistics\n\t \t ur option: '))

                if opt==1:
                    print(df)
                elif opt==2:
                    book_name=input("\t \t let's add a book \n book name: ")
                    category=input('book category: ')
                    price=float(input('book price: '))
                    quantity=int(input('quantity: '))
                    df.loc[df.index.stop]=[book_name,category,price,quantity]
                    df.to_csv('book_store.csv')
                elif opt==3:
                    df.drop(df[df['book_name']==input('\tdeleting a book \n book name: ')].index[0],axis=0)
                elif opt==4:
                    print(df['book_name'].values)
                elif opt==5:
                    print(df.describe())
                if input('exit? (y/n): ')=='y':
                    break
    elif option=='2':
        username=input('username: ')
        password=input('password: ')
        

        while True:
            book_name=input('\t hello let\'s get some books\n Enter the book name: ')
            if book_name in df['book_name'].values:
                print(f"book name: {df[df['book_name']==book_name]['book_name'].iloc[0]}",end=' ')
                print(f"book price: {df[df['book_name']==book_name]['price'].iloc[0]} $",end=' ')
                print(f"book category: {df[df['book_name']==book_name]['category'].iloc[0]}")
                if input('You would buy it? (y/n): ')== 'y':
                    df.loc[df[df['book_name']==book_name].index[0],'quantity']-=1
                    
            else:
                print('wrong book name')

            if input('continue? (y/n): ')=='n' :
                break
    elif option=='3':
        break