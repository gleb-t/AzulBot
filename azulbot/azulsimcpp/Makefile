#INC=-I ./Lib -I ~/miniconda3/include/python3.8
INC=-I ./Lib -I $(shell python -c "from sysconfig import get_paths as gp; print(gp()[\"include\"])")

default-rule: azulsim.cpp
	mkdir -p build
	$(CXX) -Wall $(INC) -g -O2 -std=c++17 -fPIC azulsim.cpp Azul.cpp AzulState.cpp -shared -o build/azulcpp.so
	cp build/azulcpp.so ../

