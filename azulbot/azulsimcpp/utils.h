#pragma once

// Hash a value and combine with another hash.
// From https://stackoverflow.com/questions/7110301/generic-hash-for-tuples-in-unordered-map-unordered-set
template <class T>
inline size_t hash_combine(size_t seed, T const& v)
{
    return seed ^ (std::hash<T>()(v) + 0x9e3779b9 + (seed << 6) + (seed >> 2));
}