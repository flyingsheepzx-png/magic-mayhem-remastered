/* Synthetic PE fixture for static analysis only; never needs to be executed. */
__declspec(dllexport) int __cdecl re_probe(int value) {
    if (value > 10) return value * 3;
    return value + 7;
}
int __cdecl entry(void) { return re_probe(5); }
