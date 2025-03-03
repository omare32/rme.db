import random
words='apple mango strewberry banana lemon watermelon'

words=words.split()




while True:
    try:
        word=random.choice(words)
        
        print('_ '*len(word))

        chances=len(word)+2

        letters_guessed=''

        while chances>0 :
            letter=input('Enter a letter')
            if len(letter)>1:
                print('input a single letter')
                chances-=1
                continue
            elif not letter.isalpha():
                print('input a letter')
                chances-=1
                continue
            elif letter in letters_guessed:
                print('u entered that letter before')
                chances-=1
                continue

            if letter in word:
                chances-=1
                letters_guessed+=letter*word.count(letter)
                if len(letters_guessed)==len(word):
                    print('word was: ',word)
                    print('u won')

                    break


            else:
                chances-=1
                print('wrong ,guess a new letter')

            for l in word:
                if l in letters_guessed:
                    print(l,end=' ')
                else:
                    print('_',end=' ')
            print()
    except KeyboardInterrupt:
            break
        
        
        
        
