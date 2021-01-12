#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>

#include "AzulState.h"

namespace py = pybind11;
using namespace pybind11::literals;

// Hash a value and combine with another hash.
// From https://stackoverflow.com/questions/7110301/generic-hash-for-tuples-in-unordered-map-unordered-set
template <class T>
inline size_t hash(size_t seed, T const& v)
{
    return seed ^ (std::hash<T>()(v) + 0x9e3779b9 + (seed << 6) + (seed >> 2));
}


PYBIND11_MODULE(azulsim, m) 
{
    m.doc() = "azulsim";

    py::enum_<Color>(m, "Color")
        .value("Empty", Color::Empty)
        .value("Blue", Color::Blue)
        .value("Yellow", Color::Yellow)
        .value("Red", Color::Red)
        .value("Black", Color::Black)
        .value("White", Color::White);

    py::class_<Move>(m, "Move")
        .def(py::init<uint8_t, Color, uint8_t>())
        .def("__repr__", [](const Move& m) 
        {
            return "<Move '" + std::to_string(m.sourceBin) + " " +
                   std::to_string(static_cast<uint8_t>(m.color)) + " " + std::to_string(m.targetQueue) + "'>";
        })
        .def("__hash__", [](const Move& m)
        {
            return hash(hash(hash(size_t{ 0 }, m.sourceBin), static_cast<uint8_t>(m.color)), m.targetQueue);
        })
        .def("__eq__", [](const Move& m1, const Move& m2)
        {
            return m1 == m2;
        });

    py::class_<PlayerState>(m, "PlayerState")
        .def(py::init())
        .def_readwrite("wall", &PlayerState::wall)
        .def_readwrite("queue", &PlayerState::queue)
        .def_readwrite("floorCount", &PlayerState::floorCount)
        .def_readwrite("score", &PlayerState::score)

        .def("set_wall", &PlayerState::set_wall)
        .def("set_queue", &PlayerState::set_queue);


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
        .def("enumerate_moves", &AzulState::enumerate_moves)
        .def_static("get_wall_slot_color", &AzulState::get_wall_slot_color);
}

