#ifndef MM_MIXED_H
#define MM_MIXED_H

/* Diagnostic compositor for the verified native-UI probe. The game owns the
 * 2560x1440 primary and paints battle only in its upper-left 1280x720 rect.
 * Keep that primary untouched: the next engine draw must see its own pixels.
 */
#include <windows.h>
#include "ddsurface.h"

BOOL mm_mixed_enabled(void);
IDirectDrawSurfaceImpl* mm_mixed_present(IDirectDrawSurfaceImpl* primary);
POINT mm_mixed_input_point(IDirectDrawSurfaceImpl* primary, int x, int y);
extern LONG mm_mixed_d3d9_uploads;

#ifdef MM_MIXED_IMPLEMENTATION
#include <string.h>
#include "dd.h"

#define MM_MIXED_ENGINE_PATH "D:\\Games\\Magic&Mayham\\modernization\\assets\\hd\\native-ui-2k-probe\\runtime\\Chaos-Wide169-engine.exe"
#define MM_MIXED_PLAYTEST_PATH "D:\\Games\\Magic&Mayham\\modernization\\playtests\\mixed-ui-v1\\game-wide169\\Chaos-Wide169-engine.exe"
#define MM_MIXED_PLAYTEST_V2_PATH "D:\\Games\\Magic&Mayham\\modernization\\playtests\\mixed-ui-v2\\game-wide169\\Chaos-Wide169-engine.exe"
#define MM_MIXED_PLAYTEST_V3_PATH "D:\\Games\\Magic&Mayham\\modernization\\playtests\\mixed-ui-v3\\game-wide169\\Chaos-Wide169-engine.exe"
#define MM_MIXED_PLAYTEST_V4_PATH "D:\\Games\\Magic&Mayham\\modernization\\playtests\\mixed-ui-v4\\game-wide169\\Chaos-Wide169-engine.exe"

static unsigned char* mm_mixed_pixels;
static SIZE_T mm_mixed_capacity;
static IDirectDrawSurfaceImpl mm_mixed_surface;
LONG mm_mixed_d3d9_uploads;

static int mm_mixed_sharpen_level(void)
{
    char value[4] = { 0 };
    GetEnvironmentVariableA("MM_PROBE_BATTLE_SHARPEN", value, sizeof(value));
    return (value[0] == '1' || value[0] == '2') && value[1] == 0 ? value[0] - '0' : 0;
}

static int mm_mixed_clamp(int value, int maximum)
{
    return value < 0 ? 0 : (value > maximum ? maximum : value);
}

/* A nearest-neighbour 2x block has three same-colour neighbours per pixel.
 * Only the horizontal and vertical neighbour outside the block differ.
 * Calculate the exact post-scale five-tap result from the 1280x720 source. */
static unsigned short mm_mixed_sharpen_pixel(unsigned short c,
                                             unsigned short horizontal,
                                             unsigned short vertical, int shift)
{
    int red = (c >> 11) & 31, green = (c >> 5) & 63, blue = c & 31;
    red = mm_mixed_clamp(red + ((2 * red - ((horizontal >> 11) & 31) - ((vertical >> 11) & 31)) >> shift), 31);
    green = mm_mixed_clamp(green + ((2 * green - ((horizontal >> 5) & 63) - ((vertical >> 5) & 63)) >> shift), 63);
    blue = mm_mixed_clamp(blue + ((2 * blue - (horizontal & 31) - (vertical & 31)) >> shift), 31);
    return (unsigned short)((red << 11) | (green << 5) | blue);
}

BOOL mm_mixed_enabled(void)
{
    static LONG state;
    LONG value = InterlockedExchangeAdd(&state, 0);
    if (!value)
    {
        char flag[4] = { 0 }, path[MAX_PATH] = { 0 };
        DWORD n = GetModuleFileNameA(NULL, path, sizeof(path));
        GetEnvironmentVariableA("MM_PROBE_MIXED_RENDER", flag, sizeof(flag));
        value = flag[0] == '1' && flag[1] == 0 && n && n < sizeof(path) &&
            (_stricmp(path, MM_MIXED_ENGINE_PATH) == 0 ||
             _stricmp(path, MM_MIXED_PLAYTEST_PATH) == 0 ||
             _stricmp(path, MM_MIXED_PLAYTEST_V2_PATH) == 0 ||
             _stricmp(path, MM_MIXED_PLAYTEST_V3_PATH) == 0 ||
             _stricmp(path, MM_MIXED_PLAYTEST_V4_PATH) == 0) ? 2 : 1;
        InterlockedExchange(&state, value);
    }
    return value == 2;
}

/* The engine keeps pixels from the preceding full-size page outside the
 * 1280x720 battle rectangle. Classify by live controls, not stale pixels. */
static BOOL mm_mixed_readable(const void* pointer, SIZE_T bytes)
{
    MEMORY_BASIC_INFORMATION memory;
    SIZE_T address = (SIZE_T)pointer;
    SIZE_T end = address + bytes;
    if (!pointer || end < address || !VirtualQuery(pointer, &memory, sizeof(memory)) ||
        memory.State != MEM_COMMIT || (memory.Protect & (PAGE_NOACCESS | PAGE_GUARD)))
        return FALSE;
    return end <= (SIZE_T)memory.BaseAddress + memory.RegionSize;
}

static BOOL mm_mixed_is_battle(IDirectDrawSurfaceImpl* primary)
{
    int count, i, battle_marker_a = 0, battle_marker_b = 0;
    if (*(volatile DWORD*)0x5E1728 != 1280 || *(volatile DWORD*)0x5E172C != 720)
        return FALSE;
    count = *(volatile int*)0x642C68;
    if (count <= 0 || count > 400) return FALSE;
    for (i = 0; i < count; ++i)
    {
        const unsigned char* control = *(const unsigned char**)(0x642034 + i * 4);
        const int* rect;
        if (!mm_mixed_readable(control, 0x21)) return FALSE;
        if (*(const DWORD*)control == 0x5C6EE8) battle_marker_a = 1;
        if (*(const DWORD*)control == 0x5C6F54) battle_marker_b = 1;
        if (*(const DWORD*)control == 0x5C6A8C) continue;
        rect = (const int*)(control + 0x11);
        if (rect[2] > 1280 || rect[3] > 720) return FALSE;
    }
    return battle_marker_a && battle_marker_b;
}

IDirectDrawSurfaceImpl* mm_mixed_present(IDirectDrawSurfaceImpl* primary)
{
    SIZE_T bytes;
    unsigned char* pixels;
    int x, y, sharpen, shift;
    if (!mm_mixed_enabled() || !primary || !primary->surface ||
        primary->width != 2560 || primary->height != 1440 || primary->bpp != 16 ||
        primary->pitch < 5120 || primary->pitch > 16384 ||
        !mm_mixed_is_battle(primary))
        return primary;
    bytes = (SIZE_T)primary->pitch * 1440;
    if (mm_mixed_capacity < bytes)
    {
        pixels = (unsigned char*)HeapAlloc(GetProcessHeap(), 0, bytes);
        if (!pixels) return primary;
        if (mm_mixed_pixels) HeapFree(GetProcessHeap(), 0, mm_mixed_pixels);
        mm_mixed_pixels = pixels;
        mm_mixed_capacity = bytes;
    }
    memset(mm_mixed_pixels, 0, bytes);
    sharpen = mm_mixed_sharpen_level();
    shift = sharpen == 1 ? 3 : 2;
    for (y = 0; y < 720; ++y)
    {
        const unsigned short* src = (const unsigned short*)((const unsigned char*)primary->surface + y * primary->pitch);
        const unsigned short* above = y ? (const unsigned short*)((const unsigned char*)primary->surface + (y - 1) * primary->pitch) : src;
        const unsigned short* below = y < 719 ? (const unsigned short*)((const unsigned char*)primary->surface + (y + 1) * primary->pitch) : src;
        unsigned short* dst0 = (unsigned short*)(mm_mixed_pixels + y * 2 * primary->pitch);
        unsigned short* dst1 = (unsigned short*)(mm_mixed_pixels + (y * 2 + 1) * primary->pitch);
        for (x = 0; x < 1280; ++x)
        {
            unsigned short c = src[x];
            if (!sharpen)
            {
                dst0[x * 2] = dst0[x * 2 + 1] = c;
                dst1[x * 2] = dst1[x * 2 + 1] = c;
            }
            else
            {
                unsigned short left = x ? src[x - 1] : c;
                unsigned short right = x < 1279 ? src[x + 1] : c;
                dst0[x * 2] = x && y ? mm_mixed_sharpen_pixel(c, left, above[x], shift) : c;
                dst0[x * 2 + 1] = y && x < 1279 ? mm_mixed_sharpen_pixel(c, right, above[x], shift) : c;
                dst1[x * 2] = x && y < 719 ? mm_mixed_sharpen_pixel(c, left, below[x], shift) : c;
                dst1[x * 2 + 1] = x < 1279 && y < 719 ? mm_mixed_sharpen_pixel(c, right, below[x], shift) : c;
            }
        }
    }
    mm_mixed_surface = *primary;
    mm_mixed_surface.surface = mm_mixed_pixels;
    return &mm_mixed_surface;
}

POINT mm_mixed_input_point(IDirectDrawSurfaceImpl* primary, int x, int y)
{
    POINT result = { x, y };
    if (mm_mixed_enabled() && primary && primary->surface && mm_mixed_is_battle(primary))
    {
        result.x /= 2;
        result.y /= 2;
    }
    return result;
}
#endif
#endif
