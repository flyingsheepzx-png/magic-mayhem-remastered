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

#endif
