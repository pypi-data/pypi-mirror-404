class numberS_type_verification_LIST:
    def is_odds(nums: list):
        returned_list = []

        for numbers in nums:
            if numbers % 2 == 1:
                returned_list.append("True")
            elif numbers % 2 == 0:
                returned_list.append("False")
            else:
                raise TypeError(f"{nums} cannot be parsed, cause it was not a number type.")
        
        return returned_list
    def is_evens(nums: list):
        returned_list = []

        for numbers in nums:
            if numbers % 2 == 0:
                returned_list.append("True")
            elif numbers % 2 == 1:
                returned_list.append("False")
            else:
                raise TypeError(f"{nums} cannot be parsed, cause it was not a number type.")
    def is_number_types(nums: list):
        returned_list = []

        for numbers in nums:
            if type(numbers) == "float":
                returned_list.append("float")
            elif type(numbers) == "int":
                returned_list.append("int")
            else:
                returned_list.append("int")
            
        return returned_list