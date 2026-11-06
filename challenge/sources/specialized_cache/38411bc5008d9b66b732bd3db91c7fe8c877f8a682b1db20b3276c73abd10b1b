#include <iostream>
#include <random>

void gen() {
    std::mt19937 rng(0x1337);
    
    for (int i = 0; i < 6; i++) {
        std::cout << rng() << "L, "; // need to be marked long for Java
    }
    std::cout << std::endl;
}

void process() {
    int stored[] = {19073894, 4056458, 20559029, 22387579, 81490990, 2530382};
    u_int32_t java_ints[] = {2193497836, 470549166, 2487642607, 2417858579, 4156040538, 290993979};
    char flag_piece[8] = {0};

    for (int i = 0; i < 6; i++) {
        flag_piece[i] = java_ints[i] / stored[i];
    }
    std::cout << flag_piece << std::endl;
}

int main() {
    // gen();
    process(); // styl3s
}

// g++ gen_bytes.cpp && ./a.out