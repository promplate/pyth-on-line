# Secrets for the app
API_KEY = "123"
PASSWORD = "<PASSWORDaaa>"
SECRET = 'asd1234asd123asdasdasd'

# Tokens
API_TOKEN = "<123>" 
MY_TOKEN = "134"


def my(a):
    b = a
    for i in range(a):
        b = i
        print(a)
    b = 100
    # assert b == 9
    import time
    time.sleep(30)
    pass

def slow_fibonacci(n):
    if n < 2:
        return n
    return slow_fibonacci(n-1) + slow_fibonacci(n-2)



def test_my():
    a = 40000
    # assert a == 40
    print("starting test")
    slow_fibonacci(39)

    # test_2()



def test_2() -> None:
    b = 50

    # for i in range("a"):
    #     b = i
    #
    # b = 10
    # assert b == 30

    # my(b)

# if __name__ == "__main__":
#     my(10)