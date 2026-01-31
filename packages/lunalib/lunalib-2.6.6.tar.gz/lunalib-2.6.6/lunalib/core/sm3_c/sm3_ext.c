#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <stdint.h>
#include <string.h>
#include <stddef.h>
#include <stdlib.h>
#if defined(_WIN32)
#include <windows.h>
#include <process.h>
#else
#include <pthread.h>
#endif
#if defined(LUNALIB_AVX2) || defined(LUNALIB_AVX512)
#include <immintrin.h>
#endif

#define ROTL32(x, n) (((x) << (n)) | ((x) >> (32 - (n))))
#define P0(x) ((x) ^ ROTL32((x), 9) ^ ROTL32((x), 17))
#define P1(x) ((x) ^ ROTL32((x), 15) ^ ROTL32((x), 23))
#define FF(x, y, z, j) (((j) < 16) ? ((x) ^ (y) ^ (z)) : (((x) & (y)) | ((x) & (z)) | ((y) & (z))))
#define GG(x, y, z, j) (((j) < 16) ? ((x) ^ (y) ^ (z)) : (((x) & (y)) | ((~(x)) & (z))))

static volatile int sm3_abort_flag = 0;

static const uint32_t SM3_IV[8] = {
    0x7380166F, 0x4914B2B9, 0x172442D7, 0xDA8A0600,
    0xA96F30BC, 0x163138AA, 0xE38DEE4D, 0xB0FB0E4E
};

static const uint32_t SM3_TJ0 = 0x79CC4519;
static const uint32_t SM3_TJ1 = 0x7A879D8A;

static uint32_t load_be32(const uint8_t* p) {
    return ((uint32_t)p[0] << 24) | ((uint32_t)p[1] << 16) | ((uint32_t)p[2] << 8) | (uint32_t)p[3];
}

static void store_be32(uint8_t* out, uint32_t v) {
    out[0] = (uint8_t)(v >> 24);
    out[1] = (uint8_t)(v >> 16);
    out[2] = (uint8_t)(v >> 8);
    out[3] = (uint8_t)(v);
}

static int sm3_check_difficulty(const uint8_t digest[32], int difficulty);

static void sm3_compress_block(const uint8_t block[64], uint32_t V[8]) {
    uint32_t W[68];
    uint32_t W1[64];
    for (int i = 0; i < 16; i++) {
        W[i] = load_be32(block + i * 4);
    }
    for (int i = 16; i < 68; i++) {
        uint32_t x = W[i - 16] ^ W[i - 9] ^ ROTL32(W[i - 3], 15);
        W[i] = P1(x) ^ ROTL32(W[i - 13], 7) ^ W[i - 6];
    }
    for (int i = 0; i < 64; i++) {
        W1[i] = W[i] ^ W[i + 4];
    }

    uint32_t A = V[0], B = V[1], C = V[2], D = V[3];
    uint32_t E = V[4], F = V[5], G = V[6], H = V[7];

    for (int j = 0; j < 64; j++) {
        uint32_t Tj = (j < 16) ? SM3_TJ0 : SM3_TJ1;
        uint32_t SS1 = ROTL32((ROTL32(A, 12) + E + ROTL32(Tj, j)) & 0xFFFFFFFF, 7);
        uint32_t SS2 = SS1 ^ ROTL32(A, 12);
        uint32_t TT1 = (FF(A, B, C, j) + D + SS2 + W1[j]) & 0xFFFFFFFF;
        uint32_t TT2 = (GG(E, F, G, j) + H + SS1 + W[j]) & 0xFFFFFFFF;
        D = C;
        C = ROTL32(B, 9);
        B = A;
        A = TT1;
        H = G;
        G = ROTL32(F, 19);
        F = E;
        E = P0(TT2);
    }

    V[0] ^= A; V[1] ^= B; V[2] ^= C; V[3] ^= D;
    V[4] ^= E; V[5] ^= F; V[6] ^= G; V[7] ^= H;
}

static void sm3_hash_bytes(const uint8_t* data, size_t len, uint8_t out[32]) {
    uint32_t V[8];
    for (int i = 0; i < 8; i++) {
        V[i] = SM3_IV[i];
    }

    size_t full_blocks = len / 64;
    for (size_t i = 0; i < full_blocks; i++) {
        sm3_compress_block(data + (i * 64), V);
    }

    uint64_t bit_len = (uint64_t)len * 8U;
    uint8_t block[64];
    size_t rem = len % 64;
    memset(block, 0, sizeof(block));
    if (rem > 0) {
        memcpy(block, data + (full_blocks * 64), rem);
    }
    block[rem] = 0x80;
    if (rem <= 55) {
        block[56] = (uint8_t)(bit_len >> 56);
        block[57] = (uint8_t)(bit_len >> 48);
        block[58] = (uint8_t)(bit_len >> 40);
        block[59] = (uint8_t)(bit_len >> 32);
        block[60] = (uint8_t)(bit_len >> 24);
        block[61] = (uint8_t)(bit_len >> 16);
        block[62] = (uint8_t)(bit_len >> 8);
        block[63] = (uint8_t)(bit_len);
        sm3_compress_block(block, V);
    } else {
        sm3_compress_block(block, V);
        memset(block, 0, sizeof(block));
        block[56] = (uint8_t)(bit_len >> 56);
        block[57] = (uint8_t)(bit_len >> 48);
        block[58] = (uint8_t)(bit_len >> 40);
        block[59] = (uint8_t)(bit_len >> 32);
        block[60] = (uint8_t)(bit_len >> 24);
        block[61] = (uint8_t)(bit_len >> 16);
        block[62] = (uint8_t)(bit_len >> 8);
        block[63] = (uint8_t)(bit_len);
        sm3_compress_block(block, V);
    }

    for (int i = 0; i < 8; i++) {
        store_be32(out + (i * 4), V[i]);
    }
}

static void sm3_prepare_compact_base(const uint8_t* base80, uint32_t V0[8], uint8_t block1[64]) {
    for (int i = 0; i < 8; i++) {
        V0[i] = SM3_IV[i];
    }

    uint8_t block0[64];
    memcpy(block0, base80, 64);

    memset(block1, 0, 64);
    memcpy(block1, base80 + 64, 16);
    block1[24] = 0x80;
    block1[56] = 0x00;
    block1[57] = 0x00;
    block1[58] = 0x00;
    block1[59] = 0x00;
    block1[60] = 0x00;
    block1[61] = 0x00;
    block1[62] = 0x02;
    block1[63] = 0xC0;

    sm3_compress_block(block0, V0);
}

static void sm3_hash_compact_88_with_state(const uint32_t V0[8], uint8_t block1[64], uint64_t nonce, uint8_t out[32]) {
    uint32_t V[8];
    for (int i = 0; i < 8; i++) {
        V[i] = V0[i];
    }

    block1[16] = (uint8_t)(nonce >> 56);
    block1[17] = (uint8_t)(nonce >> 48);
    block1[18] = (uint8_t)(nonce >> 40);
    block1[19] = (uint8_t)(nonce >> 32);
    block1[20] = (uint8_t)(nonce >> 24);
    block1[21] = (uint8_t)(nonce >> 16);
    block1[22] = (uint8_t)(nonce >> 8);
    block1[23] = (uint8_t)(nonce);

    sm3_compress_block(block1, V);

    for (int i = 0; i < 8; i++) {
        store_be32(out + (i * 4), V[i]);
    }
}

static void sm3_hash_compact_88_bytes(const uint8_t* base80, uint64_t nonce, uint8_t out[32]) {
    uint32_t V0[8];
    uint8_t block1[64];
    sm3_prepare_compact_base(base80, V0, block1);
    sm3_hash_compact_88_with_state(V0, block1, nonce, out);
}

#if defined(LUNALIB_AVX512)
static int sm3_mine_compact_avx512(const uint8_t* base80, uint64_t start_nonce, uint64_t count, int difficulty, uint64_t* out_nonce);
#endif
#if defined(LUNALIB_AVX2)
static int sm3_mine_compact_avx2(const uint8_t* base80, uint64_t start_nonce, uint64_t count, int difficulty, uint64_t* out_nonce);
#endif

static int sm3_try_set_found(volatile int* flag, uint64_t* out_nonce, uint64_t nonce) {
#if defined(_WIN32)
    if (InterlockedCompareExchange((volatile LONG*)flag, 1, 0) == 0) {
        *out_nonce = nonce;
        return 1;
    }
    return 0;
#else
    if (__sync_bool_compare_and_swap(flag, 0, 1)) {
        *out_nonce = nonce;
        return 1;
    }
    return 0;
#endif
}

static int sm3_mine_compact_range(const uint8_t* base80, uint64_t start_nonce, uint64_t count, int difficulty,
                                  volatile int* found_flag, uint64_t* found_nonce) {
    const uint64_t chunk = 4096;
    uint64_t offset = 0;
    while (offset < count) {
        if (*found_flag || sm3_abort_flag) {
            return 0;
        }
        uint64_t remaining = count - offset;
        uint64_t batch = remaining < chunk ? remaining : chunk;
        uint64_t nonce = start_nonce + offset;

#if defined(LUNALIB_AVX512)
        if (batch >= 16) {
            uint64_t out_nonce = 0;
            if (sm3_mine_compact_avx512(base80, nonce, batch, difficulty, &out_nonce)) {
                sm3_try_set_found(found_flag, found_nonce, out_nonce);
                return 1;
            }
            offset += batch;
            continue;
        }
#endif

#if defined(LUNALIB_AVX2)
        if (batch >= 8) {
            uint64_t out_nonce = 0;
            if (sm3_mine_compact_avx2(base80, nonce, batch, difficulty, &out_nonce)) {
                sm3_try_set_found(found_flag, found_nonce, out_nonce);
                return 1;
            }
            offset += batch;
            continue;
        }
#endif

        for (uint64_t i = 0; i < batch; i++) {
            if (*found_flag || sm3_abort_flag) {
                return 0;
            }
            uint8_t digest[32];
            uint64_t current = nonce + i;
            sm3_hash_compact_88_bytes(base80, current, digest);
            if (sm3_check_difficulty(digest, difficulty)) {
                sm3_try_set_found(found_flag, found_nonce, current);
                return 1;
            }
        }
        offset += batch;
    }
    return 0;
}

typedef struct {
    const uint8_t* base80;
    uint64_t start_nonce;
    uint64_t count;
    int difficulty;
    volatile int* found_flag;
    uint64_t* found_nonce;
} sm3_thread_ctx;

#if defined(_WIN32)
static unsigned __stdcall sm3_worker_thread(void* arg) {
    sm3_thread_ctx* ctx = (sm3_thread_ctx*)arg;
    sm3_mine_compact_range(ctx->base80, ctx->start_nonce, ctx->count, ctx->difficulty, ctx->found_flag, ctx->found_nonce);
    return 0;
}
#else
static void* sm3_worker_thread(void* arg) {
    sm3_thread_ctx* ctx = (sm3_thread_ctx*)arg;
    sm3_mine_compact_range(ctx->base80, ctx->start_nonce, ctx->count, ctx->difficulty, ctx->found_flag, ctx->found_nonce);
    return NULL;
}
#endif

static void sm3_mine_compact_mt(const uint8_t* base80, uint64_t start_nonce, uint64_t count, int difficulty,
                                unsigned int threads, volatile int* found_flag, uint64_t* found_nonce) {
    if (threads <= 1 || count == 0) {
        sm3_mine_compact_range(base80, start_nonce, count, difficulty, found_flag, found_nonce);
        return;
    }
#if defined(_WIN32)
    if (threads > 64) {
        threads = 64;
    }
#endif
    if (count < (uint64_t)threads) {
        threads = (unsigned int)count;
        if (threads == 0) {
            return;
        }
    }

    uint64_t base = start_nonce;
    uint64_t per = count / threads;
    uint64_t rem = count % threads;

#if defined(_WIN32)
    HANDLE* handles = (HANDLE*)calloc(threads, sizeof(HANDLE));
    sm3_thread_ctx* ctxs = (sm3_thread_ctx*)calloc(threads, sizeof(sm3_thread_ctx));
    if (!handles || !ctxs) {
        if (handles) free(handles);
        if (ctxs) free(ctxs);
        sm3_mine_compact_range(base80, start_nonce, count, difficulty, found_flag, found_nonce);
        return;
    }
    unsigned int handle_count = 0;
    for (unsigned int i = 0; i < threads; i++) {
        uint64_t span = per + (i < rem ? 1 : 0);
        ctxs[i].base80 = base80;
        ctxs[i].start_nonce = base;
        ctxs[i].count = span;
        ctxs[i].difficulty = difficulty;
        ctxs[i].found_flag = found_flag;
        ctxs[i].found_nonce = found_nonce;
        base += span;
        unsigned thread_id = 0;
        HANDLE h = (HANDLE)_beginthreadex(NULL, 0, sm3_worker_thread, &ctxs[i], 0, &thread_id);
        if (!h) {
            sm3_mine_compact_range(ctxs[i].base80, ctxs[i].start_nonce, ctxs[i].count, ctxs[i].difficulty, found_flag, found_nonce);
        } else {
            handles[handle_count++] = h;
        }
    }

    DWORD wait_count = (DWORD)handle_count;
    DWORD idx = 0;
    while (idx < wait_count) {
        DWORD batch = (wait_count - idx > MAXIMUM_WAIT_OBJECTS) ? MAXIMUM_WAIT_OBJECTS : (wait_count - idx);
        WaitForMultipleObjects(batch, handles + idx, TRUE, INFINITE);
        idx += batch;
    }
    for (unsigned int i = 0; i < handle_count; i++) {
        CloseHandle(handles[i]);
    }
    free(handles);
    free(ctxs);
#else
    pthread_t* threads_arr = (pthread_t*)calloc(threads, sizeof(pthread_t));
    sm3_thread_ctx* ctxs = (sm3_thread_ctx*)calloc(threads, sizeof(sm3_thread_ctx));
    if (!threads_arr || !ctxs) {
        if (threads_arr) free(threads_arr);
        if (ctxs) free(ctxs);
        sm3_mine_compact_range(base80, start_nonce, count, difficulty, found_flag, found_nonce);
        return;
    }
    for (unsigned int i = 0; i < threads; i++) {
        uint64_t span = per + (i < rem ? 1 : 0);
        ctxs[i].base80 = base80;
        ctxs[i].start_nonce = base;
        ctxs[i].count = span;
        ctxs[i].difficulty = difficulty;
        ctxs[i].found_flag = found_flag;
        ctxs[i].found_nonce = found_nonce;
        base += span;
        if (pthread_create(&threads_arr[i], NULL, sm3_worker_thread, &ctxs[i]) != 0) {
            sm3_mine_compact_range(ctxs[i].base80, ctxs[i].start_nonce, ctxs[i].count, ctxs[i].difficulty, found_flag, found_nonce);
        }
    }
    for (unsigned int i = 0; i < threads; i++) {
        pthread_join(threads_arr[i], NULL);
    }
    free(threads_arr);
    free(ctxs);
#endif
}

#if defined(LUNALIB_AVX512)
static inline __m512i rotl32_avx512(__m512i x, int n) {
    return _mm512_or_si512(_mm512_slli_epi32(x, n), _mm512_srli_epi32(x, 32 - n));
}

static inline __m512i p0_avx512(__m512i x) {
    return _mm512_xor_si512(_mm512_xor_si512(x, rotl32_avx512(x, 9)), rotl32_avx512(x, 17));
}

static inline __m512i p1_avx512(__m512i x) {
    return _mm512_xor_si512(_mm512_xor_si512(x, rotl32_avx512(x, 15)), rotl32_avx512(x, 23));
}

static inline void sm3_round_avx512(int j, const __m512i* W, const __m512i* W1,
                                    __m512i* A, __m512i* B, __m512i* C, __m512i* D,
                                    __m512i* E, __m512i* F, __m512i* G, __m512i* H) {
    uint32_t Tj = (j < 16) ? SM3_TJ0 : SM3_TJ1;
    uint32_t Tj_rot = (Tj << (j & 31)) | (Tj >> (32 - (j & 31)));
    __m512i Tjv = _mm512_set1_epi32((int)Tj_rot);
    __m512i SS1 = rotl32_avx512(_mm512_add_epi32(_mm512_add_epi32(rotl32_avx512(*A, 12), *E), Tjv), 7);
    __m512i SS2 = _mm512_xor_si512(SS1, rotl32_avx512(*A, 12));

    __m512i FFv;
    __m512i GGv;
    if (j < 16) {
        FFv = _mm512_xor_si512(_mm512_xor_si512(*A, *B), *C);
        GGv = _mm512_xor_si512(_mm512_xor_si512(*E, *F), *G);
    } else {
        FFv = _mm512_or_si512(_mm512_or_si512(_mm512_and_si512(*A, *B), _mm512_and_si512(*A, *C)), _mm512_and_si512(*B, *C));
        GGv = _mm512_or_si512(_mm512_and_si512(*E, *F), _mm512_andnot_si512(*E, *G));
    }

    __m512i TT1 = _mm512_add_epi32(_mm512_add_epi32(_mm512_add_epi32(FFv, *D), SS2), W1[j]);
    __m512i TT2 = _mm512_add_epi32(_mm512_add_epi32(_mm512_add_epi32(GGv, *H), SS1), W[j]);

    *D = *C;
    *C = rotl32_avx512(*B, 9);
    *B = *A;
    *A = TT1;
    *H = *G;
    *G = rotl32_avx512(*F, 19);
    *F = *E;
    *E = p0_avx512(TT2);
}

static int sm3_mine_compact_avx512(const uint8_t* base80, uint64_t start_nonce, uint64_t count, int difficulty, uint64_t* out_nonce) {
    if (count < 16) {
        return 0;
    }

    uint32_t V0[8];
    uint8_t block1[64];
    sm3_prepare_compact_base(base80, V0, block1);

    const uint32_t w0 = load_be32(block1 + 0);
    const uint32_t w1 = load_be32(block1 + 4);
    const uint32_t w2 = load_be32(block1 + 8);
    const uint32_t w3 = load_be32(block1 + 12);

    __m512i W[68];
    __m512i W1[64];

    const __m512i W0 = _mm512_set1_epi32((int)w0);
    const __m512i W1c = _mm512_set1_epi32((int)w1);
    const __m512i W2 = _mm512_set1_epi32((int)w2);
    const __m512i W3 = _mm512_set1_epi32((int)w3);
    const __m512i W6 = _mm512_set1_epi32((int)0x80000000u);
    const __m512i WZ = _mm512_set1_epi32(0);
    const __m512i W15 = _mm512_set1_epi32((int)0x000002C0u);

    uint64_t i = 0;
    while (i + 16 <= count) {
        uint32_t w4_arr[16];
        uint32_t w5_arr[16];
        uint64_t nonces[16];
        for (int lane = 0; lane < 16; lane++) {
            uint64_t nonce = start_nonce + i + (uint64_t)lane;
            nonces[lane] = nonce;
            w4_arr[lane] = (uint32_t)(nonce >> 32);
            w5_arr[lane] = (uint32_t)(nonce & 0xFFFFFFFFu);
        }

        __m512i W4 = _mm512_loadu_si512((const void*)w4_arr);
        __m512i W5 = _mm512_loadu_si512((const void*)w5_arr);

        W[0] = W0;
        W[1] = W1c;
        W[2] = W2;
        W[3] = W3;
        W[4] = W4;
        W[5] = W5;
        W[6] = W6;
        W[7] = WZ;
        W[8] = WZ;
        W[9] = WZ;
        W[10] = WZ;
        W[11] = WZ;
        W[12] = WZ;
        W[13] = WZ;
        W[14] = WZ;
        W[15] = W15;

        for (int j = 16; j < 68; j++) {
            __m512i x = _mm512_xor_si512(W[j - 16], _mm512_xor_si512(W[j - 9], rotl32_avx512(W[j - 3], 15)));
            W[j] = _mm512_xor_si512(p1_avx512(x), _mm512_xor_si512(rotl32_avx512(W[j - 13], 7), W[j - 6]));
        }
        for (int j = 0; j < 64; j++) {
            W1[j] = _mm512_xor_si512(W[j], W[j + 4]);
        }

        __m512i A = _mm512_set1_epi32((int)V0[0]);
        __m512i B = _mm512_set1_epi32((int)V0[1]);
        __m512i C = _mm512_set1_epi32((int)V0[2]);
        __m512i D = _mm512_set1_epi32((int)V0[3]);
        __m512i E = _mm512_set1_epi32((int)V0[4]);
        __m512i F = _mm512_set1_epi32((int)V0[5]);
        __m512i G = _mm512_set1_epi32((int)V0[6]);
        __m512i H = _mm512_set1_epi32((int)V0[7]);

        for (int j = 0; j < 64; j += 8) {
            sm3_round_avx512(j, W, W1, &A, &B, &C, &D, &E, &F, &G, &H);
            sm3_round_avx512(j + 1, W, W1, &A, &B, &C, &D, &E, &F, &G, &H);
            sm3_round_avx512(j + 2, W, W1, &A, &B, &C, &D, &E, &F, &G, &H);
            sm3_round_avx512(j + 3, W, W1, &A, &B, &C, &D, &E, &F, &G, &H);
            sm3_round_avx512(j + 4, W, W1, &A, &B, &C, &D, &E, &F, &G, &H);
            sm3_round_avx512(j + 5, W, W1, &A, &B, &C, &D, &E, &F, &G, &H);
            sm3_round_avx512(j + 6, W, W1, &A, &B, &C, &D, &E, &F, &G, &H);
            sm3_round_avx512(j + 7, W, W1, &A, &B, &C, &D, &E, &F, &G, &H);
        }

        uint32_t a[16], b[16], c[16], d[16], e[16], f[16], g[16], h[16];
        _mm512_storeu_si512((void*)a, A);
        _mm512_storeu_si512((void*)b, B);
        _mm512_storeu_si512((void*)c, C);
        _mm512_storeu_si512((void*)d, D);
        _mm512_storeu_si512((void*)e, E);
        _mm512_storeu_si512((void*)f, F);
        _mm512_storeu_si512((void*)g, G);
        _mm512_storeu_si512((void*)h, H);

        for (int lane = 0; lane < 16; lane++) {
            uint8_t digest[32];
            store_be32(digest + 0, V0[0] ^ a[lane]);
            store_be32(digest + 4, V0[1] ^ b[lane]);
            store_be32(digest + 8, V0[2] ^ c[lane]);
            store_be32(digest + 12, V0[3] ^ d[lane]);
            store_be32(digest + 16, V0[4] ^ e[lane]);
            store_be32(digest + 20, V0[5] ^ f[lane]);
            store_be32(digest + 24, V0[6] ^ g[lane]);
            store_be32(digest + 28, V0[7] ^ h[lane]);
            if (sm3_check_difficulty(digest, difficulty)) {
                *out_nonce = nonces[lane];
                return 1;
            }
        }

        i += 16;
    }
    return 0;
}
#endif

#if defined(LUNALIB_AVX2)
static inline __m256i rotl32_avx2(__m256i x, int n) {
    return _mm256_or_si256(_mm256_slli_epi32(x, n), _mm256_srli_epi32(x, 32 - n));
}

static inline __m256i p0_avx2(__m256i x) {
    return _mm256_xor_si256(_mm256_xor_si256(x, rotl32_avx2(x, 9)), rotl32_avx2(x, 17));
}

static inline __m256i p1_avx2(__m256i x) {
    return _mm256_xor_si256(_mm256_xor_si256(x, rotl32_avx2(x, 15)), rotl32_avx2(x, 23));
}

static inline void sm3_round_avx2(int j, const __m256i* W, const __m256i* W1,
                                  __m256i* A, __m256i* B, __m256i* C, __m256i* D,
                                  __m256i* E, __m256i* F, __m256i* G, __m256i* H) {
    uint32_t Tj = (j < 16) ? SM3_TJ0 : SM3_TJ1;
    uint32_t Tj_rot = (Tj << (j & 31)) | (Tj >> (32 - (j & 31)));
    __m256i Tjv = _mm256_set1_epi32((int)Tj_rot);
    __m256i SS1 = rotl32_avx2(_mm256_add_epi32(_mm256_add_epi32(rotl32_avx2(*A, 12), *E), Tjv), 7);
    __m256i SS2 = _mm256_xor_si256(SS1, rotl32_avx2(*A, 12));

    __m256i FFv;
    __m256i GGv;
    if (j < 16) {
        FFv = _mm256_xor_si256(_mm256_xor_si256(*A, *B), *C);
        GGv = _mm256_xor_si256(_mm256_xor_si256(*E, *F), *G);
    } else {
        FFv = _mm256_or_si256(_mm256_or_si256(_mm256_and_si256(*A, *B), _mm256_and_si256(*A, *C)), _mm256_and_si256(*B, *C));
        GGv = _mm256_or_si256(_mm256_and_si256(*E, *F), _mm256_andnot_si256(*E, *G));
    }

    __m256i TT1 = _mm256_add_epi32(_mm256_add_epi32(_mm256_add_epi32(FFv, *D), SS2), W1[j]);
    __m256i TT2 = _mm256_add_epi32(_mm256_add_epi32(_mm256_add_epi32(GGv, *H), SS1), W[j]);

    *D = *C;
    *C = rotl32_avx2(*B, 9);
    *B = *A;
    *A = TT1;
    *H = *G;
    *G = rotl32_avx2(*F, 19);
    *F = *E;
    *E = p0_avx2(TT2);
}

static int sm3_mine_compact_avx2(const uint8_t* base80, uint64_t start_nonce, uint64_t count, int difficulty, uint64_t* out_nonce) {
    if (count < 8) {
        return 0;
    }

    uint32_t V0[8];
    uint8_t block1[64];
    sm3_prepare_compact_base(base80, V0, block1);

    const uint32_t w0 = load_be32(block1 + 0);
    const uint32_t w1 = load_be32(block1 + 4);
    const uint32_t w2 = load_be32(block1 + 8);
    const uint32_t w3 = load_be32(block1 + 12);

    __m256i W[68];
    __m256i W1[64];

    const __m256i W0 = _mm256_set1_epi32((int)w0);
    const __m256i W1c = _mm256_set1_epi32((int)w1);
    const __m256i W2 = _mm256_set1_epi32((int)w2);
    const __m256i W3 = _mm256_set1_epi32((int)w3);
    const __m256i W6 = _mm256_set1_epi32((int)0x80000000u);
    const __m256i WZ = _mm256_set1_epi32(0);
    const __m256i W15 = _mm256_set1_epi32((int)0x000002C0u);

    uint64_t i = 0;
    while (i + 8 <= count) {
        uint32_t w4_arr[8];
        uint32_t w5_arr[8];
        uint64_t nonces[8];
        for (int lane = 0; lane < 8; lane++) {
            uint64_t nonce = start_nonce + i + (uint64_t)lane;
            nonces[lane] = nonce;
            w4_arr[lane] = (uint32_t)(nonce >> 32);
            w5_arr[lane] = (uint32_t)(nonce & 0xFFFFFFFFu);
        }

        __m256i W4 = _mm256_loadu_si256((const __m256i*)w4_arr);
        __m256i W5 = _mm256_loadu_si256((const __m256i*)w5_arr);

        W[0] = W0;
        W[1] = W1c;
        W[2] = W2;
        W[3] = W3;
        W[4] = W4;
        W[5] = W5;
        W[6] = W6;
        W[7] = WZ;
        W[8] = WZ;
        W[9] = WZ;
        W[10] = WZ;
        W[11] = WZ;
        W[12] = WZ;
        W[13] = WZ;
        W[14] = WZ;
        W[15] = W15;

        for (int j = 16; j < 68; j++) {
            __m256i x = _mm256_xor_si256(W[j - 16], _mm256_xor_si256(W[j - 9], rotl32_avx2(W[j - 3], 15)));
            W[j] = _mm256_xor_si256(p1_avx2(x), _mm256_xor_si256(rotl32_avx2(W[j - 13], 7), W[j - 6]));
        }
        for (int j = 0; j < 64; j++) {
            W1[j] = _mm256_xor_si256(W[j], W[j + 4]);
        }

        __m256i A = _mm256_set1_epi32((int)V0[0]);
        __m256i B = _mm256_set1_epi32((int)V0[1]);
        __m256i C = _mm256_set1_epi32((int)V0[2]);
        __m256i D = _mm256_set1_epi32((int)V0[3]);
        __m256i E = _mm256_set1_epi32((int)V0[4]);
        __m256i F = _mm256_set1_epi32((int)V0[5]);
        __m256i G = _mm256_set1_epi32((int)V0[6]);
        __m256i H = _mm256_set1_epi32((int)V0[7]);

        for (int j = 0; j < 64; j += 8) {
            sm3_round_avx2(j, W, W1, &A, &B, &C, &D, &E, &F, &G, &H);
            sm3_round_avx2(j + 1, W, W1, &A, &B, &C, &D, &E, &F, &G, &H);
            sm3_round_avx2(j + 2, W, W1, &A, &B, &C, &D, &E, &F, &G, &H);
            sm3_round_avx2(j + 3, W, W1, &A, &B, &C, &D, &E, &F, &G, &H);
            sm3_round_avx2(j + 4, W, W1, &A, &B, &C, &D, &E, &F, &G, &H);
            sm3_round_avx2(j + 5, W, W1, &A, &B, &C, &D, &E, &F, &G, &H);
            sm3_round_avx2(j + 6, W, W1, &A, &B, &C, &D, &E, &F, &G, &H);
            sm3_round_avx2(j + 7, W, W1, &A, &B, &C, &D, &E, &F, &G, &H);
        }

        uint32_t a[8], b[8], c[8], d[8], e[8], f[8], g[8], h[8];
        _mm256_storeu_si256((__m256i*)a, A);
        _mm256_storeu_si256((__m256i*)b, B);
        _mm256_storeu_si256((__m256i*)c, C);
        _mm256_storeu_si256((__m256i*)d, D);
        _mm256_storeu_si256((__m256i*)e, E);
        _mm256_storeu_si256((__m256i*)f, F);
        _mm256_storeu_si256((__m256i*)g, G);
        _mm256_storeu_si256((__m256i*)h, H);

        for (int lane = 0; lane < 8; lane++) {
            uint8_t digest[32];
            store_be32(digest + 0, V0[0] ^ a[lane]);
            store_be32(digest + 4, V0[1] ^ b[lane]);
            store_be32(digest + 8, V0[2] ^ c[lane]);
            store_be32(digest + 12, V0[3] ^ d[lane]);
            store_be32(digest + 16, V0[4] ^ e[lane]);
            store_be32(digest + 20, V0[5] ^ f[lane]);
            store_be32(digest + 24, V0[6] ^ g[lane]);
            store_be32(digest + 28, V0[7] ^ h[lane]);
            if (sm3_check_difficulty(digest, difficulty)) {
                *out_nonce = nonces[lane];
                return 1;
            }
        }

        i += 8;
    }
    return 0;
}
#endif

static int sm3_check_difficulty(const uint8_t digest[32], int difficulty) {
    if (difficulty <= 0) {
        return 1;
    }
    int full_bytes = difficulty / 2;
    int half = difficulty & 1;
    for (int i = 0; i < full_bytes; i++) {
        if (digest[i] != 0) {
            return 0;
        }
    }
    if (half) {
        if ((digest[full_bytes] & 0xF0) != 0) {
            return 0;
        }
    }
    return 1;
}

static PyObject* py_sm3_digest(PyObject* self, PyObject* args) {
    Py_buffer buf;
    if (!PyArg_ParseTuple(args, "y*", &buf)) {
        return NULL;
    }
    uint8_t out[32];
    sm3_hash_bytes((const uint8_t*)buf.buf, (size_t)buf.len, out);
    PyBuffer_Release(&buf);
    return PyBytes_FromStringAndSize((const char*)out, 32);
}

static PyObject* py_sm3_hash_compact_88(PyObject* self, PyObject* args) {
    Py_buffer base;
    unsigned long long nonce;
    if (!PyArg_ParseTuple(args, "y*K", &base, &nonce)) {
        return NULL;
    }
    if (base.len != 80) {
        PyBuffer_Release(&base);
        PyErr_SetString(PyExc_ValueError, "base80 must be 80 bytes");
        return NULL;
    }
    uint8_t out[32];
    sm3_hash_compact_88_bytes((const uint8_t*)base.buf, (uint64_t)nonce, out);
    PyBuffer_Release(&base);
    return PyBytes_FromStringAndSize((const char*)out, 32);
}

static PyObject* py_sm3_mine_compact(PyObject* self, PyObject* args) {
    Py_buffer base;
    unsigned long long start_nonce;
    unsigned long long count;
    int difficulty;
    unsigned int threads = 1;
    if (!PyArg_ParseTuple(args, "y*KKi|I", &base, &start_nonce, &count, &difficulty, &threads)) {
        return NULL;
    }
    if (base.len != 80) {
        PyBuffer_Release(&base);
        PyErr_SetString(PyExc_ValueError, "base80 must be 80 bytes");
        return NULL;
    }
    if (count == 0 || sm3_abort_flag) {
        PyBuffer_Release(&base);
        Py_RETURN_NONE;
    }

    volatile int found = 0;
    unsigned long long found_nonce = 0;
    const uint8_t* base80 = (const uint8_t*)base.buf;
    if (threads < 1) {
        threads = 1;
    }

    Py_BEGIN_ALLOW_THREADS
    if (threads <= 1) {
        sm3_mine_compact_range(base80, (uint64_t)start_nonce, (uint64_t)count, difficulty, &found, (uint64_t*)&found_nonce);
    } else {
        sm3_mine_compact_mt(base80, (uint64_t)start_nonce, (uint64_t)count, difficulty, threads, &found, (uint64_t*)&found_nonce);
    }
    Py_END_ALLOW_THREADS

    PyBuffer_Release(&base);
    if (!found) {
        Py_RETURN_NONE;
    }
    return PyLong_FromUnsignedLongLong(found_nonce);
}

static PyObject* py_sm3_set_abort(PyObject* self, PyObject* args) {
    int flag = 0;
    if (!PyArg_ParseTuple(args, "p", &flag)) {
        return NULL;
    }
    sm3_abort_flag = flag ? 1 : 0;
    Py_RETURN_NONE;
}

static PyMethodDef Sm3Methods[] = {
    {"sm3_digest", py_sm3_digest, METH_VARARGS, "Compute SM3 digest."},
    {"sm3_hash_compact_88", py_sm3_hash_compact_88, METH_VARARGS, "Compute SM3 for compact 80-byte base + nonce."},
    {"sm3_mine_compact", py_sm3_mine_compact, METH_VARARGS, "Search nonce range for SM3 difficulty (compact header)."},
    {"sm3_set_abort", py_sm3_set_abort, METH_VARARGS, "Set/clear SM3 mining abort flag."},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef sm3module = {
    PyModuleDef_HEAD_INIT,
    "sm3_ext",
    "SM3 CPU extension",
    -1,
    Sm3Methods
};

PyMODINIT_FUNC PyInit_sm3_ext(void) {
    return PyModule_Create(&sm3module);
}