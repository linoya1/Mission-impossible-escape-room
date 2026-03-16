#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

namespace py = pybind11;

// MSVC-friendly version: without __int128 (fully sufficient for small n such as 3233)
static long long modexp(long long base, long long exp, long long mod) {
    long long res = 1 % mod;
    base %= mod;
    while (exp > 0) {
        if (exp & 1LL) res = (res * base) % mod;
        base = (base * base) % mod;
        exp >>= 1LL;
    }
    return res;
}

// Decrypts each "byte" separately: c^d mod n
std::vector<int> rsa_decrypt_bytes(const std::vector<int>& cipher_bytes, long long d, long long n) {
    std::vector<int> out;
    out.reserve(cipher_bytes.size());
    for (int c : cipher_bytes) {
        out.push_back((int)modexp(c, d, n));
    }
    return out;
}

PYBIND11_MODULE(rsa_cpp, m) {
    m.def("rsa_decrypt_bytes", &rsa_decrypt_bytes, "RSA decrypt per-byte (toy)");
}
