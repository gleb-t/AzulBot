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


PYBIND11_MODULE(azulcpp, m) 
{
    m.doc() = "azulcpp";

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
        .def("set_wall_row", &PlayerState::set_wall_row)
        .def("set_wall_col", &PlayerState::set_wall_col)
        .def("set_queue", &PlayerState::set_queue);

    py::class_<AzulState>(m, "AzulState")
        .def(py::init())

        .def_readwrite("bag", &AzulState::bag)
        .def_readwrite("bins", &AzulState::bins)
        .def_readwrite("players", &AzulState::players)
        .def_readwrite("nextPlayer", &AzulState::nextPlayer)
        .def_readwrite("firstPlayer", &AzulState::firstPlayer)
        .def_readwrite("poolWasTouched", &AzulState::poolWasTouched)

        .def("copy", &AzulState::copy)
        .def("set_bin", &AzulState::set_bin);

    py::class_<MoveOutcome>(m, "MoveOutcome")
        .def(py::init<const AzulState&, bool, bool>())
        .def_readwrite("state", &MoveOutcome::state)
        .def_readwrite("isRandom", &MoveOutcome::isRandom)
        .def_readwrite("isEnd", &MoveOutcome::isEnd);


    py::class_<Azul>(m, "Azul")
        .def(py::init())
        .def_readonly_static("ColorNumber", &Azul::ColorNumber)
        .def_readonly_static("TileNumber", &Azul::TileNumber)
        .def_readonly_static("PlayerNumber", &Azul::PlayerNumber)
        .def_readonly_static("BinNumber", &Azul::BinNumber)
        .def_readonly_static("BinSize", &Azul::BinSize)
        .def_readonly_static("WallSize", &Azul::WallSize)
        .def_readonly_static("FloorSize", &Azul::FloorSize)
        .def_readonly_static("FloorScores", &Azul::FloorScores)

        .def("enumerate_moves", &Azul::enumerate_moves)
        .def("apply_move", &Azul::apply_move)
        .def("is_game_end", &Azul::is_game_end)

        .def("deal_round", &Azul::deal_round, py::arg("state"), py::arg("fixedSampled") = std::vector<Color>{})
        .def("_refill_bag", &Azul::_refill_bag)
        .def_static("get_wall_slot_color", &Azul::get_wall_slot_color);
}

