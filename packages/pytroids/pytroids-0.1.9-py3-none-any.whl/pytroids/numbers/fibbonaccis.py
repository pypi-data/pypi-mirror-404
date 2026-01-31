class fibbonacci:
    @staticmethod

    def generate_fibbonacci(start1: float, start2: float, steps: int):
        if steps in (0, 1):
            raise IndexError("Steps can't be 0 or 1")
        
        num1 = start1
        num2 = start2
        count = 0
        sequence = []

        while count < steps:
            sequence.append(num1)
            num1, num2 = num2, num1 + num2
            count += 1

        return sequence
    def infinite_fibbonacci(start1: float, start2: float):
        import math

        steps = math.inf
        if steps in (0, 1):
            raise IndexError("Steps can't be 0 or 1")
        
        num1 = start1
        num2 = start2
        count = 0
        sequence = []

        while count < steps:
            sequence.append(num1)
            num1, num2 = num2, num1 + num2
            count += 1
            print(sequence)

if __name__ == "__main__":
    fibbonacci.infinite_fibbonacci(0, 1)