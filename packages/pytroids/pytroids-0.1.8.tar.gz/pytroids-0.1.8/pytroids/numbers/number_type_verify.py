class number_type_verification:
    @staticmethod

    def is_odd(num: int):
        if num % 2 == 1:
            return True
        else:
            return False
    def is_even(num: int):
        if num % 2 == 0:
            return True
        else:
            return False
    def num_type(num):
        if type(num) == "int":
            return "Integer"
        elif type(num) == "float":
            return "Float"
        else:
            raise TypeError(f"{num} cannot be parsed, cause it was not a number type.")