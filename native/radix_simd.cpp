/**
 * Radix-style small-prime filtering using Apple M-series NEON
 * ------------------------------------------------------------
 * This sample is a self-contained C++ translation of the 8-lane
 * SIMD snippet you provided. It demonstrates how dual 4-wide
 * NEON registers can be used to sieve integers against a bank of
 * small primes before falling back to scalar primality checks.
 *
 * The code is intentionally standalone: it stubs the "prime_system"
 * helpers with a simple deterministic check, computes Barrett
 * constants on the fly, and exposes a tiny CLI driver. Compile it on
 * Apple silicon with:
 *
 *   clang++ -std=c++20 -O3 -march=armv8.5-a+simd \
 *           -o radix_simd native/radix_simd.cpp
 *
 * (For older Apple chips use -mcpu=apple-m4 or the appropriate target.)
 */

#include <arm_neon.h>

#include <array>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <iomanip>
#include <iostream>
#include <vector>

namespace {
constexpr std::array<uint32_t, 8> kSmallPrimes{2, 3, 5, 7, 11, 13, 17, 19};
constexpr std::array<uint32_t, 8> kExtendedPrimes{23, 29, 31, 37, 41, 43, 47, 53};

constexpr uint32_t make_barrett_magic(uint32_t p) {
    return static_cast<uint32_t>((static_cast<uint64_t>(1ULL << 32) + p - 1) / p);
}

inline void barrett_modq_u32_dual(
    uint32x4_t n_vec1, uint32x4_t n_vec2,
    uint32x4_t magic_vec, uint32x4_t p_vec,
    uint32x4_t& remainder1, uint32x4_t& remainder2) {

    uint64x2_t lo1 = vmull_u32(vget_low_u32(n_vec1), vget_low_u32(magic_vec));
    uint64x2_t hi1 = vmull_u32(vget_high_u32(n_vec1), vget_high_u32(magic_vec));
    uint64x2_t lo2 = vmull_u32(vget_low_u32(n_vec2), vget_low_u32(magic_vec));
    uint64x2_t hi2 = vmull_u32(vget_high_u32(n_vec2), vget_high_u32(magic_vec));

    uint32x2_t q_low1 = vshrn_n_u64(lo1, 32);
    uint32x2_t q_high1 = vshrn_n_u64(hi1, 32);
    uint32x2_t q_low2 = vshrn_n_u64(lo2, 32);
    uint32x2_t q_high2 = vshrn_n_u64(hi2, 32);

    uint32x4_t q_vec1 = vcombine_u32(q_low1, q_high1);
    uint32x4_t q_vec2 = vcombine_u32(q_low2, q_high2);

    uint32x4_t qp_vec1 = vmulq_u32(q_vec1, p_vec);
    uint32x4_t qp_vec2 = vmulq_u32(q_vec2, p_vec);

    remainder1 = vsubq_u32(n_vec1, qp_vec1);
    remainder2 = vsubq_u32(n_vec2, qp_vec2);

    uint32x4_t cmp1 = vcgeq_u32(remainder1, p_vec);
    uint32x4_t cmp2 = vcgeq_u32(remainder2, p_vec);
    remainder1 = vsubq_u32(remainder1, vandq_u32(cmp1, p_vec));
    remainder2 = vsubq_u32(remainder2, vandq_u32(cmp2, p_vec));
}

bool is_prime_scalar(uint64_t n) {
    if (n < 2) {
        return false;
    }
    if (n % 2 == 0) {
        return n == 2;
    }
    for (uint64_t i = 3; i * i <= n; i += 2) {
        if (n % i == 0) {
            return false;
        }
    }
    return true;
}

class SIMDBatchProcessor {
public:
    void process(const std::vector<uint64_t>& numbers, std::vector<bool>& results) {
        results.resize(numbers.size());
        const uint64_t* aligned_numbers = numbers.data();

        if (numbers.size() >= 16) {
            process_batch_simd_real_8lane(aligned_numbers, results.data(), numbers.size());
        } else {
            process_scalar(aligned_numbers, results.data(), numbers.size());
        }
    }

private:
    void process_scalar(const uint64_t* numbers, bool* results, size_t count) {
        for (size_t i = 0; i < count; ++i) {
            results[i] = is_prime_scalar(numbers[i]);
        }
    }

    void process_batch_simd_real_8lane(const uint64_t* numbers, bool* results, size_t count) {
        const uint64_t* aligned_numbers = numbers;

        for (size_t i = 0; i + 8 <= count; i += 8) {
            uint32_t nums1[4];
            uint32_t nums2[4];
            bool can_use_neon = true;
            for (int j = 0; j < 8; ++j) {
                if (aligned_numbers[i + j] > UINT32_MAX) {
                    can_use_neon = false;
                    break;
                }
            }
            if (!can_use_neon) {
                process_scalar(&aligned_numbers[i], &results[i], 8);
                continue;
            }

            for (int j = 0; j < 4; ++j) {
                nums1[j] = static_cast<uint32_t>(aligned_numbers[i + j]);
                nums2[j] = static_cast<uint32_t>(aligned_numbers[i + 4 + j]);
            }

            uint32x4_t n_vec1 = vld1q_u32(nums1);
            uint32x4_t n_vec2 = vld1q_u32(nums2);
            uint32x4_t composite_mask1 = vdupq_n_u32(0);
            uint32x4_t composite_mask2 = vdupq_n_u32(0);

            auto sieve = [&](uint32_t prime) {
                uint32x4_t p_vec = vdupq_n_u32(prime);
                uint32x4_t m_vec = vdupq_n_u32(make_barrett_magic(prime));

                uint32x4_t r_vec1, r_vec2;
                barrett_modq_u32_dual(n_vec1, n_vec2, m_vec, p_vec, r_vec1, r_vec2);

                uint32x4_t divisible1 = vceqq_u32(r_vec1, vdupq_n_u32(0));
                uint32x4_t divisible2 = vceqq_u32(r_vec2, vdupq_n_u32(0));

                uint32x4_t is_prime_itself1 = vceqq_u32(n_vec1, p_vec);
                uint32x4_t is_prime_itself2 = vceqq_u32(n_vec2, p_vec);
                divisible1 = vandq_u32(divisible1, vmvnq_u32(is_prime_itself1));
                divisible2 = vandq_u32(divisible2, vmvnq_u32(is_prime_itself2));

                composite_mask1 = vorrq_u32(composite_mask1, divisible1);
                composite_mask2 = vorrq_u32(composite_mask2, divisible2);
            };

            for (auto prime : kSmallPrimes) {
                sieve(prime);
            }
            for (auto prime : kExtendedPrimes) {
                sieve(prime);
            }

            std::array<uint32_t, 4> composite_flags1{};
            std::array<uint32_t, 4> composite_flags2{};
            vst1q_u32(composite_flags1.data(), composite_mask1);
            vst1q_u32(composite_flags2.data(), composite_mask2);

            for (int j = 0; j < 4; ++j) {
                if (composite_flags1[j]) {
                    results[i + j] = false;
                } else {
                    results[i + j] = is_prime_scalar(aligned_numbers[i + j]);
                }
            }
            for (int j = 0; j < 4; ++j) {
                if (composite_flags2[j]) {
                    results[i + 4 + j] = false;
                } else {
                    results[i + 4 + j] = is_prime_scalar(aligned_numbers[i + 4 + j]);
                }
            }
        }

        size_t remaining = count % 8;
        if (remaining) {
            process_scalar(&numbers[count - remaining], &results[count - remaining], remaining);
        }
    }
};

}  // namespace

int main(int argc, char** argv) {
    if (argc < 2) {
        std::cerr << "Usage: ./radix_simd <n1> <n2> ...\n";
        return 1;
    }

    std::vector<uint64_t> numbers;
    for (int i = 1; i < argc; ++i) {
        numbers.emplace_back(std::strtoull(argv[i], nullptr, 10));
    }

    std::vector<bool> results;
    SIMDBatchProcessor processor;
    processor.process(numbers, results);

    std::cout << "SIMD sieve results:\n";
    for (size_t i = 0; i < numbers.size(); ++i) {
        std::cout << std::setw(12) << numbers[i] << " -> "
                  << (results[i] ? "prime" : "composite") << '\n';
    }
    return 0;
}
