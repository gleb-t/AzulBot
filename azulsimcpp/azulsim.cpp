#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>

#include "AzulState.h"

namespace py = pybind11;
using namespace pybind11::literals;

int test(int a)
{
	return a + 5;
}


PYBIND11_MODULE(azulsim, m) 
{
    m.doc() = "azulsim";

    m.def("test", &test, "Test", py::arg("a"));

    py::enum_<Color>(m, "Color")
        .value("Empty", Color::Empty)
        .value("Blue", Color::Blue)
        .value("Yellow", Color::Yellow)
        .value("Red", Color::Red)
        .value("Black", Color::Black)
        .value("White", Color::White);

    py::class_<Move>(m, "Move")
        .def(py::init<uint8_t, Color, uint8_t>());

    py::class_<PlayerState>(m, "PlayerState")
        .def(py::init())
        .def_readwrite("wall", &PlayerState::wall)
        .def_readwrite("queue", &PlayerState::queue)
        .def_readwrite("floorCount", &PlayerState::floorCount)
        .def_readwrite("score", &PlayerState::score);

    py::class_<AzulState>(m, "AzulState")
        .def(py::init())
        .def_readonly_static("ColorNumber", &AzulState::ColorNumber)
        .def_readonly_static("TileNumber", &AzulState::TileNumber)
        .def_readonly_static("PlayerNumber", &AzulState::PlayerNumber)
        .def_readonly_static("BinNumber", &AzulState::BinNumber)
        .def_readonly_static("BinSize", &AzulState::BinSize)
        .def_readonly_static("WallSize", &AzulState::WallSize)
        .def_readonly_static("FloorSize", &AzulState::FloorSize)
        .def_readonly_static("FloorScores", &AzulState::FloorScores)

        .def_readwrite("bag", &AzulState::bag)
        .def_readwrite("bins", &AzulState::bins)
        .def_readwrite("players", &AzulState::players)
        .def_readwrite("nextPlayer", &AzulState::nextPlayer)
        .def_readwrite("firstPlayer", &AzulState::firstPlayer)
        .def_readwrite("poolWasTouched", &AzulState::poolWasTouched)

        .def("set_bin", &AzulState::set_bin)
        .def("enumerate_moves", &AzulState::enumerate_moves);
}

