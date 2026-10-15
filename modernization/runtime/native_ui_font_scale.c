/* Isolated Chinese font probe. No CRT, globals, imports, or absolute addresses.
 * The existing chaos95 resolver still handles encoding and glyph cache lookup.
 * A caller-owned scratch area holds the decoded coverage and scaled RLE frame.
 * The native software text blitter consumes the returned frame synchronously.
 */
typedef unsigned char u8;
typedef unsigned int u32;
typedef int i32;

u8 * __cdecl hd_chinese_frame(const u8 *source, u8 *scratch)
{
    const u32 *header = (const u32 *)source;
    u32 width, height, size;
    u32 x, y, i, position, cursor, pixels, run, paint;
    u8 *grid = scratch;
    u8 *row = scratch + 4096;
    u8 *out = scratch + 4224;
    u32 *result = (u32 *)out;
    u32 next;
#ifdef MM_SCREEN_FONT_ENABLE
    /* The mixed-font hook sets 1 for the native battle and 2 for full UI.
     * Zero retains enlarged UI text before the hook is ready. */
    if (*(volatile u32 *)(scratch + 32764) == 1) return (u8 *)source;
#endif
    if (!source) return (u8 *)source;
    width = header[1]; height = header[2]; size = header[0];
    if (width == 0 || height == 0 || width > 64 || height > 64 ||
        size < 40 + height * 8 || size > 2500)
        return (u8 *)source;
    for (i = 0; i < 4096; ++i) ((volatile u8 *)grid)[i] = 0;
    for (y = 0; y < height; ++y) {
        cursor = ((const u32 *)(source + 40))[y * 2];
        pixels = ((const u32 *)(source + 40))[y * 2 + 1];
        position = 0;
        paint = 0;
        while (position < width) {
            if (cursor >= size) return (u8 *)source;
            run = source[cursor++];
            if (run > width - position) return (u8 *)source;
            if (paint) {
                if (pixels + run > size) return (u8 *)source;
                for (i = 0; i < run; ++i) grid[y * 64 + position + i] = source[pixels++];
            }
            position += run;
            paint ^= 1;
        }
    }
    for (i = 0; i < 10; ++i) result[i] = header[i];
    result[1] = width * 2;
    result[2] = height * 2;
    result[3] = (u32)((i32)header[3] * 2);
    result[4] = (u32)((i32)header[4] * 2);
    next = 40 + height * 16;
    for (y = 0; y < height * 2; ++y) {
        u32 sy = y / 2, sy1 = sy + (sy + 1 < height);
        for (x = 0; x < width * 2; ++x) {
            u32 sx = x / 2, sx1 = sx + (sx + 1 < width);
            u32 value = grid[sy * 64 + sx];
            if (x & 1) value += grid[sy * 64 + sx1];
            else value *= 2;
            if (y & 1) {
                u32 other = grid[sy1 * 64 + sx];
                if (x & 1) other += grid[sy1 * 64 + sx1];
                else other *= 2;
                value += other;
            } else value *= 2;
            row[x] = (u8)((value + 2) / 4);
        }
        ((u32 *)(out + 40))[y * 2] = next;
        position = 0;
        paint = 0;
        while (position < width * 2) {
            run = 0;
            while (position + run < width * 2 && (u32)(row[position + run] != 0) == paint) ++run;
            out[next++] = (u8)run;
            position += run;
            paint ^= 1;
        }
        ((u32 *)(out + 40))[y * 2 + 1] = next;
        for (x = 0; x < width * 2; ++x) if (row[x]) out[next++] = row[x];
    }
    result[0] = next;
    return out;
}
