#ifndef FROZEN_CUB_ORDERED_SET_H
#define FROZEN_CUB_ORDERED_SET_H

#include <Python.h>

class OrderedSet {
    public:
        OrderedSet(PyObject* iterable = nullptr) { 
            dict = PyDict_New();
            if (iterable == nullptr) { return; }

            PyObject* iterator = PyObject_GetIter(iterable);
            if (iterator == nullptr) { PyErr_Clear();   return; }

            PyObject* item;
            int result;

            while ((result = PyIter_NextItem(iterator, &item)) == 1) {
                add(item);
                Py_DECREF(item);
            }
            Py_DECREF(iterator);
        }

        ~OrderedSet() { Py_DECREF(dict); }

        bool add(PyObject* item) {
            if (PyDict_Contains(dict, item)) { return false; }
            PyDict_SetItem(dict, item, Py_None);
            return true;
        }

        bool contains(PyObject* item) { return PyDict_Contains(dict, item); }
        Py_ssize_t size() { return PyDict_Size(dict); }
        PyObject* get_iter() { return PyObject_GetIter(dict); }
        PyObject* get_keys() { PyObject* keys = PyDict_Keys(dict); return keys; }

    private:
        PyObject* dict;
};

class FrozenOrderedSet : public OrderedSet {
    public:
        FrozenOrderedSet(PyObject* iterable = nullptr) : OrderedSet(iterable) {}
        FrozenOrderedSet(const OrderedSet& other) : OrderedSet(other) {}
        bool add(PyObject* item) = delete;
};

#endif /* FROZEN_CUB_ORDERED_SET_H */
