#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>

#include "AzulState.h"
#include "MctsBot.h"
#include "utils.h"

namespace py = pybind11;
using namespace pybind11::literals;



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
        .def_readwrite("sourceBin", &Move::sourceBin)
        .def_readwrite("color", &Move::color)
        .def_readwrite("targetQueue", &Move::targetQueue)
        .def("__repr__", [](const Move& m) 
        {
            return "<Move '" + std::to_string(m.sourceBin) + " " +
                   std::to_string(static_cast<uint8_t>(m.color)) + " " + std::to_string(m.targetQueue) + "'>";
        })
        .def("__hash__", [](const Move& m)
        {
            return hash_combine(hash_combine(hash_combine(size_t{ 0 }, m.sourceBin), static_cast<uint8_t>(m.color)), m.targetQueue);
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
        .def("set_queue", &PlayerState::set_queue)

        .def("__eq__", [](const PlayerState& p1, const PlayerState& p2) { return p1 == p2;})
        .def("__hash__", &PlayerState::hash)
        .def(py::pickle(  // Implement the pickling methods to support copy.deepcopy.
            [](const PlayerState& p) { // __getstate__
                return py::make_tuple(p.wall, p.queue, p.floorCount, p.score);
            },
            [](py::tuple t) { // __setstate__
                if (t.size() != 4)
                    throw std::runtime_error("Invalid state length.");
                
                PlayerState p{};
                p.wall = t[0].cast<std::array<std::array<Color, Azul::WallSize>, Azul::WallSize>>();
                p.queue = t[1].cast<std::array<std::array<uint8_t, 2>, Azul::WallSize>>();
                p.floorCount = t[2].cast<uint8_t>();
                p.score = t[3].cast<uint32_t>();

                return p;
            }
        ));


    py::class_<AzulState>(m, "AzulState")
        .def(py::init())

        .def_readwrite("bag", &AzulState::bag)
        .def_readwrite("bins", &AzulState::bins)
        .def_readwrite("players", &AzulState::players)
        .def_readwrite("nextPlayer", &AzulState::nextPlayer)
        .def_readwrite("firstPlayer", &AzulState::firstPlayer)
        .def_readwrite("poolWasTouched", &AzulState::poolWasTouched)
        .def_readwrite("roundIndex", &AzulState::roundIndex)
        .def_readwrite("turnIndex", &AzulState::turnIndex)


        .def("copy", &AzulState::copy)
        .def("set_bin", &AzulState::set_bin)
        .def("__eq__", [](const AzulState& s1, const AzulState& s2) { return s1 == s2; })
        .def("__hash__", &AzulState::hash);

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
        .def_readonly_static("ScorePerRow", &Azul::ScorePerRow)
        .def_readonly_static("ScorePerColumn", &Azul::ScorePerColumn)
        .def_readonly_static("ScorePerColor", &Azul::ScorePerColor)

        .def("enumerate_moves", &Azul::enumerate_moves)
        .def("apply_move", &Azul::apply_move)
        .def("apply_move_without_scoring", &Azul::apply_move_without_scoring)
        .def("playout", &Azul::playout, py::arg("state"), py::arg("maxRoundTimeout") = 100)
        .def("is_game_end", &Azul::is_game_end, py::arg("state"))
        .def("is_round_end", &Azul::is_round_end, py::arg("state"))
        .def("get_score", &Azul::get_score)

        .def("deal_round", &Azul::deal_round, py::arg("state"), py::arg("fixedSampled") = std::vector<Color>{})
        .def("score_round", &Azul::score_round)
        .def("score_game", &Azul::score_game)
        .def("_refill_bag", &Azul::_refill_bag)
        .def_static("get_wall_slot_color", &Azul::get_wall_slot_color);

    py::class_<MctsBot>(m, "MctsBot")
        .def(py::init<Azul&, const AzulState&, int, double_t>(), 
             py::arg("azul"), py::arg("state"), py::arg("samplingWidth") = 10, py::arg("explorationWeight") = 1 / 1.4142)
        .def("step", &MctsBot::step)
        .def("step_n", &MctsBot::step_n)
        .def("get_best_move", &MctsBot::get_best_move);

}

