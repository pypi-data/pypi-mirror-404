#include <pybind11/pybind11.h>
#include "ordered_set.hpp"

namespace py = pybind11;

PYBIND11_MODULE(ordered_set, m) {
    m.doc() = "OrderedSet and FrozenOrderedSet classes, OrderedDict like behavior.";

    py::class_<OrderedSet>(m, "OrderedSet")
        .def(py::init<>())                  // OrderedSet()
        .def(py::init<PyObject *>())        // OrderedSet([1,2,3])
        .def("add", &OrderedSet::add)
        .def("has", &OrderedSet::contains)
        .def("keys", &OrderedSet::get_keys)
        .def("__contains__", &OrderedSet::contains)
        .def("__len__", &OrderedSet::size)
        .def("__iter__", &OrderedSet::get_iter);

    py::class_<FrozenOrderedSet, OrderedSet>(m, "FrozenOrderedSet")
        .def(py::init<>())                      // FrozenOrderedSet()
        .def(py::init<PyObject *>())            // FrozenOrderedSet([1,2,3])
        .def(py::init<const OrderedSet &>());   // FrozenOrderedSet(other_set)
}