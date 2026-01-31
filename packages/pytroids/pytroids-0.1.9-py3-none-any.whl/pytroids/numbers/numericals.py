class numerical_operations:
    def add(*numbers: float):
        return sum(numbers)
    def subtract(*numbers: float):
        res = numbers[0]

        for nums in numbers[:1]:
            res -= nums
        
        return res
    def multiply(*numbers: float):
        res = numbers[0]

        for nums in numbers[:1]:
            res *= nums
        
        return res
    def power(*numbers: float):
        res = numbers[0]

        for nums in numbers[1:]:
            res = pow(res, nums)
        
        return res
    def divide(*numbers: float):
        res = numbers[0]

        for nums in numbers[:1]:
            res /= nums
        
        return res
    def floor_divide(*numbers: float):
        res = numbers[0]

        for nums in numbers[:1]:
            res //= nums
        
        return res
    def modulo(*numbers: float):
        res = numbers[0]

        for nums in numbers[:1]:
            res %= nums
        
        return res