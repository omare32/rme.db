import pandas as pd

csv_name = 'bookstore_database.csv'
try:
    with open(csv_name, 'r') as file:
        pass #needed for with statement to work properly
except FileNotFoundError as e:
    print('File does not exit, "bookstore_database.csv" will be created')
    with open(csv_name, 'w') as file:
        file.write('book_name,Category,Price,Quantity' + '\n')
        file.write('bk1,medicine,22.5,5')

login = input('Do you want to login as an admin (y/n): ')

if login.lower() == 'y':
    is_admin = False
    username_master = 'AdminBS1'
    pass_master = '123BS0'
    username = input('Please enter a username: ')
    password = input('Please enter your password: ')

    if username_master == username and pass_master == password:
        is_admin = True
        print('Login Successful!')
        services = ['1-View current database', '2-Edit Database', '3-Get stats', '4-Search for a book']
        options = '\n'.join(services)
        user_choice = input(f'Please enter the number corresponding to the service you want to execute:\n{options}\n')

        if user_choice == '1':
            df = pd.read_csv('bookstore_database.csv')
            books_available = '\n'.join([f'Book({i+1}): {item}' for i, item in enumerate(df["book_name"].tolist())])
            print(f'Available books:\n{books_available}')
        elif user_choice == '2':
            services2 = ['1-Add a book', '2-Remove a book']
            options2 = '\n'.join(services2)
            user_choice2 = input(f'Please enter the number that corresponds to your choice: \n{options2}\n')
            if user_choice2 == '1':
                new_book_name = input('Please enter new book name: ')
                new_cat = input('Please enter new book category: ')
                new_price = input('Please enter new book price: ')
                new_qty = input('Please enter new book quantity: ')
                new_row = [new_book_name, new_cat, new_price, new_qty]
                df = pd.read_csv('bookstore_database.csv')
                df.loc[len(df)] = new_row
                print(df.to_string(index=False))
            elif user_choice2 == '2':
                book_dlt = input('Please enter the exact name of the book that you would like to delete: ')
                df = pd.read_csv('bookstore_database.csv')
                df = df.drop(df[df['book_name'] == book_dlt].index)
                print(df.to_string(index=False))
            write_to_file_choice = input('Are you sure you want to save your modifications to "bookstore_database.csv"? (y\n)')
            if write_to_file_choice.lower() == 'y':
                with open('bookstore_database.csv', 'w') as file:
                    file.write(df.to_csv(index=False, lineterminator='\n'))
        elif user_choice == '3':
            df = pd.read_csv('bookstore_database.csv')
            print('You can find some combined stats below \n')
            print('=============================')
            print(df.describe())
        elif user_choice == '4':
            book_name = input('Please enter a book name: ')
            with open(csv_name, 'r') as file:
                tbl = []
                header = next(file)  
                for line in file.readlines():
                    row = line.strip().split(',')
                    tbl.append(row)
                found_book = False
                for row in tbl:
                    if row[0] == book_name:
                        row[3] = str(int(row[3]) - 1)
                        found_book = True
                if not found_book:
                    print('Book not found in database.')

            user_write_choice = input('Would you like to save your changes (y/n)?')
            if user_write_choice == 'y':
                with open(csv_name, 'w') as file:
                    file.write(header)  # write the header row back to the file
                    for row in tbl:
                        line = ",".join(row) + '\n'
                        file.write(line)
        else:
            print('Invalid input. Please enter a valid choice.')
    else:
        print('Login Unsuccessful!')
        exit()
else:
    print('You are signed in as a User')
    book_name = input('Please enter a book name to search for: ')
    with open(csv_name, 'r') as file:
        tbl = []
        header = next(file)
        for line in file.readlines():
            row = line.strip().split(',')
            tbl.append(row)
        found_book = False
        for row in tbl:
            if row[0] == book_name:
                row[3] = str(int(row[3]) - 1)
                found_book = True
        if not found_book:
            print('Book not found in database.')
    user_write_choice = input('Would you like to save your changes (y/n)?')
    if user_write_choice == 'y':
        with open(csv_name, 'w') as file:
            file.write(header)
            for row in tbl:
                line = ",".join(row) + '\n'
                file.write(line)