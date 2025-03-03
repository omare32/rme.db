def spy_game(l):
    seq=[0,0,7]
    for i in l:
        if i ==seq[0] and i==7:
            print(True)
            break
        elif i==seq[0]:
            seq.remove(seq[0])
    else:
        print(False)     
        
def got33(l):
    for i in range(len(l)-1):
        if [l[i],l[i+1]]==[3,3]:
            print(True)
            break
    else:
        print(False)