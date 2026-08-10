/* Combined Zero-ADC + CDM firmware validation on Cortex-M33 (STM32L552, Renode).
 * Implements the exact pipeline from the papers:
 *   wake (analog trigger, modeled) -> MXR hash -> 32x masked Collatz -> g=floor(log2 n)
 *   -> FIR output from the physically-present window (Markov-compliant recovery)
 * Results written to SRAM markers; Renode reads them via sysbus ReadWord.
 */
#include <stdint.h>

#define MASK64 0xFFFFFFFFFFFFFFFFULL
#define GOLDEN64 0x9E3779B97F4A7C15ULL
#define MXR_MUL  0xBF58476D1CE4E5B9ULL

static volatile uint32_t *const M = (volatile uint32_t *)0x20000040U;

/* Real sensor window: UCI household power, quantized int16 (from gen_golden.py) */
static const int16_t WIN[64] = {
1482,1523,1518,1503,1486,831,546,1193,1440,1443,1428,523,514,525,530,508,
500,541,680,923,1587,1361,1578,1357,1570,1566,1571,1591,1588,1604,1793,2517,
2491,2500,2490,2498,2497,2550,2547,2564,2561,2199,2388,2573,2179,1376,1135,
1508,1524,1272,1266,1917,2424,2095,2197,2425,1558,992,1276,1378,1436,933,1314,1255};

static const int16_t COEFFS[8] = {8,24,40,56,56,40,24,8};

static inline uint64_t rotl64(uint64_t x, int r) {
    return (x << r) | (x >> (64 - r));
}

static uint64_t mxr64(uint64_t i, uint64_t j, uint64_t layer, uint64_t salt) {
    uint64_t h = GOLDEN64 ^ salt;
    uint64_t v[3] = {i, j, layer};
    for (int k = 0; k < 3; k++) {
        h ^= v[k];
        for (int r = 0; r < 2; r++) {
            h *= MXR_MUL;
            h ^= rotl64(h, 31);
        }
    }
    h ^= (h >> 33);
    h *= MXR_MUL;
    h ^= (h >> 29);
    return h;
}

static uint64_t collatz32(uint64_t n) {
    for (int it = 0; it < 32; it++) {
        n = (n & 1) ? ((3 * n + 1) & MASK64) : (n >> 1);
    }
    return n;
}

static uint32_t bit_log2(uint64_t n) {
    uint32_t g = 0;
    while (n >>= 1) g++;
    return g;
}

int main(void) {
    /* ---- wake event: re-derive state token from physical window ---- */
    uint64_t tok = mxr64((uint16_t)WIN[63], (uint16_t)WIN[62], 0, 42);
    uint64_t n = collatz32(tok);
    uint32_t g = bit_log2(n);

    /* ---- FIR output from the physically-present window ---- */
    int32_t acc = 0;
    for (int k = 0; k < 8; k++)
        acc += (int32_t)WIN[63 - k] * COEFFS[k];
    int32_t fir = acc >> 8;

    /* ---- determinism check: re-derive twice more ---- */
    uint32_t det = 1;
    for (int r = 0; r < 2; r++) {
        uint64_t t2 = mxr64((uint16_t)WIN[63], (uint16_t)WIN[62], 0, 42);
        if (bit_log2(collatz32(t2)) != g) det = 0;
    }

    /* ---- golden comparison (values from Python reference) ---- */
    uint32_t fir_ok = (fir == 1264);
    uint32_t tok_ok = ((uint32_t)(tok & 0xFFFFFFFFU) == 1988686553U);
    uint32_t g_ok   = (g == 60U);

    M[0] = 0x5C4DF1E9U;                 /* signature */
    M[1] = (uint32_t)(tok & 0xFFFFFFFFU);
    M[2] = g;
    M[3] = (uint32_t)fir;
    M[4] = det;
    M[5] = fir_ok;
    M[6] = tok_ok;
    M[7] = g_ok;
    M[8] = (fir_ok & tok_ok & g_ok & det) ? 0xA11CA55EU : 0xBAD0BAD0U;
    for (;;) ;
}

extern int main(void);
__attribute__((used)) void Reset_Handler(void) { main(); for (;;) ; }
void NMI_Handler(void) __attribute__((weak, alias("Default_Handler")));
void HardFault_Handler(void) __attribute__((weak, alias("Default_Handler")));
__attribute__((used)) void Default_Handler(void) { for (;;) ; }

/* Minimal vector table: initial SP inside 192KB SRAM, reset vector */
__attribute__((section(".isr_vector"), used))
const uint32_t vectors[4] = {
    0x20030000U,
    (uint32_t)Reset_Handler,
    (uint32_t)NMI_Handler,
    (uint32_t)HardFault_Handler,
};
