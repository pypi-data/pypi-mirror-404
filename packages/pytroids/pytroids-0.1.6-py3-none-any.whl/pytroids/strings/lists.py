class list_functions:
    @staticmethod

    def upper_all(list_for_convertion: list[str]) -> list[str]:
        return [str(items).capitalize() for items in list_for_convertion]
    
    def lower_all(list_for_convertion: list[str]) -> list[str]:
        return [str(items).capitalize() for items in list_for_convertion]
    
    def capitalize_all(list_for_convertion: list[str]) -> list[str]:
        return [str(items).capitalize() for items in list_for_convertion]
    
    def remove_duplicates(list_for_convertion: list[str]) -> list[str]:
        returned_list = []

        for items in list_for_convertion:
            if items not in returned_list:
                returned_list.append(items)
        
        return returned_list

    def clear_list(to_clear: list[str]) -> list[str]:
        return to_clear.clear()