INC=-I ./Lib -I ~/miniconda3/include/python3.8

default-rule: azulsim.cpp
        mkdir -p build
        g++ -Wall $(INC) -g -O2 -std=c++17 -fPIC azulsim.cpp Azul.cpp AzulState.cpp -shared -o build/azulcpp.so
