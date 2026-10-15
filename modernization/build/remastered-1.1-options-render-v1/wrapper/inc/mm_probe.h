#ifndef MM_PROBE_H
#define MM_PROBE_H

/* Diagnostic only: records game surface uploads separately from wrapper presents. */
static void mm_probe_event(char event_code)
{
    static HANDLE log_file = INVALID_HANDLE_VALUE;
    char line[96];
    DWORD written;
    int length;

    if (log_file == INVALID_HANDLE_VALUE)
    {
        log_file = CreateFileA("modernization\\logs\\wrapper-probe.csv",
                               FILE_APPEND_DATA, FILE_SHARE_READ | FILE_SHARE_WRITE,
                               NULL, OPEN_ALWAYS, FILE_ATTRIBUTE_NORMAL, NULL);
        if (log_file == INVALID_HANDLE_VALUE)
            return;
        if (GetFileSize(log_file, NULL) == 0)
        {
            const char header[] = "qpc,event\r\n";
            WriteFile(log_file, header, sizeof(header) - 1, &written, NULL);
        }
    }
    {
        LARGE_INTEGER tick;
        QueryPerformanceCounter(&tick);
        length = _snprintf(line, sizeof(line), "%I64d,%c\r\n", tick.QuadPart, event_code);
        if (length > 0)
            WriteFile(log_file, line, (DWORD)length, &written, NULL);
    }
}

/* Diagnostic hash of the exact game surface consumed at an upload. This
 * counts unique source images, not successful presents or distinct output
 * frames. It deliberately ignores row padding; 8-bit palette changes need
 * separate handling before interpreting the hash as a visual identity. */
static void mm_probe_frame_hash(const void* pixels, int pitch, int width, int height, int bytes_pp)
{
    if (GetEnvironmentVariableA("MM_PROBE_LIGHT", NULL, 0)) return;
    static HANDLE hash_file = INVALID_HANDLE_VALUE;
    const unsigned char* row = (const unsigned char*)pixels;
    unsigned hash = 2166136261u;
    int y, x, row_bytes, length;
    DWORD written;
    char line[128];
    LARGE_INTEGER tick;

    if (!row || width <= 0 || height <= 0 || width > 8192 || height > 8192 ||
        bytes_pp <= 0 || bytes_pp > 4 || pitch < width * bytes_pp)
        return;
    row_bytes = width * bytes_pp;
    for (y = 0; y < height; ++y, row += pitch)
        for (x = 0; x < row_bytes; ++x)
            hash = (hash ^ row[x]) * 16777619u;

    if (hash_file == INVALID_HANDLE_VALUE)
    {
        hash_file = CreateFileA("modernization\\logs\\frame-hash.csv",
                                FILE_APPEND_DATA, FILE_SHARE_READ | FILE_SHARE_WRITE,
                                NULL, OPEN_ALWAYS, FILE_ATTRIBUTE_NORMAL, NULL);
        if (hash_file == INVALID_HANDLE_VALUE)
            return;
        if (GetFileSize(hash_file, NULL) == 0)
        {
            const char header[] = "qpc,hash,width,height,bytes_pp\r\n";
            WriteFile(hash_file, header, sizeof(header) - 1, &written, NULL);
        }
    }
    QueryPerformanceCounter(&tick);
    length = _snprintf(line, sizeof(line), "%I64d,%08x,%d,%d,%d\r\n",
                       tick.QuadPart, hash, width, height, bytes_pp);
    if (length > 0 && length < sizeof(line))
        WriteFile(hash_file, line, (DWORD)length, &written, NULL);
}

#endif
