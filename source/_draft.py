"""
(c) Vitaly Smirnov [VSdev]
mrmaybelately@gmail.com
2024
"""

from dataclasses import dataclass
from lights_core import *


class Class1:
    def __init__(self, value1: any, value2: any):
        self._value1 = value1
        self._value2 = value2
        self.__value3 = 118

    @property
    def value3(self):
        return self.__value3
    
    @property
    def value1(self):
        return self._value1
    
    # @value1.getter
    # def value1(self):
    #     return self.value1
    
    @value1.setter
    def value1(self, value: any):
        self._value1 = value
    

    def get_value2(self):
        return self._value2
    
    def set_value2(self, value: any):
        self._value2 = value

    value2 = property(get_value2, set_value2)

    def __getitem__(self, key):
        return self.__value3
    
    def __setitem__(self, key, value):
        print("__setitem__", key)
        self.__value3 = value



def main():
    def e(i, j) -> None:
        print(f"{i}, {j}")
    list1 = [[e(i, j) for i in range(3)] for j in range(4)]
    print(list1)


if __name__ == '__main__':
    main()
