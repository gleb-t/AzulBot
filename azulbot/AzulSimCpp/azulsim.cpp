
#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>

namespace py = pybind11;


int test(int a)
{
	return a + 5;
}


PYBIND11_MODULE(azulsim, m) 
{
    m.doc() = "Azulsim";

    m.def("test", &test, "Test", py::arg("a"));
}

