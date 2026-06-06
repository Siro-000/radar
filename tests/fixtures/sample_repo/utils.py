def add(a, b):
    return a + b


def greet(name):
    message = f"Hello, {name}!"
    print(message)
    return message


def short():
    pass


def calculate_discount(price, pct):
    if pct < 0 or pct > 100:
        raise ValueError("Discount must be between 0 and 100")
    discount = price * pct / 100
    return price - discount


class MyClass:
    def method_one(self):
        result = []
        for i in range(10):
            result.append(i * 2)
        return result

    def method_two(self, x, y):
        squared_x = x ** 2
        squared_y = y ** 2
        return squared_x + squared_y
