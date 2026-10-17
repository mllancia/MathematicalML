def buildSquareArray (n):
    a = [] # initialize array of length n
    for i in range(n):
        a.append(i**2) # set values to i^2
    return a # return array

def binararySearch (a, d): # a is the array, d is the value to search for
    low = 0 # low index
    high = len(a) - 1 # high index
    while low <= high: # while low index is less than or equal to high index
        mid = (low + high) // 2 # mid index
        if a[mid] == d: # if mid value is equal to d
            return "Found at index: " + str(mid) # return mid index
        elif a[mid] < d: # if mid value is less than d
            low = mid + 1 # set low index to mid index + 1
        else: # if mid value is greater than d
            high = mid - 1 # set low index to midindex - 1
    return "Cannot be found"


def main():
    length = int(input("How long should our Array be? "))
    d = int(input("Which number do you want to search for? "))
    a = buildSquareArray(length)
    print(binararySearch(a, d))


main()