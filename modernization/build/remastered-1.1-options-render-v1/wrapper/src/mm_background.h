#ifndef MM_BACKGROUND_H
#define MM_BACKGROUND_H

/* Opt-in diagnostic input, entirely inside this process. Native game-client
 * coordinates bypass wrapper scaling. Never moves/clips the desktop cursor. */
BOOL mm_background_enabled(void);
UINT mm_background_message(void);
extern LONG mm_background_buttons;
extern LONG mm_background_x;
extern LONG mm_background_y;

#ifdef MM_BACKGROUND_IMPLEMENTATION
LONG mm_background_buttons;
LONG mm_background_x;
LONG mm_background_y;
BOOL mm_background_enabled(void)
{
    static LONG state;
    LONG cached = InterlockedExchangeAdd(&state, 0);
    if (!cached)
    {
        char value[4] = { 0 };
        GetEnvironmentVariableA("MM_PROBE_BACKGROUND_INPUT", value, sizeof(value));
        cached = value[0] == '1' && value[1] == 0 ? 2 : 1;
        InterlockedExchange(&state, cached);
    }
    return cached == 2;
}
UINT mm_background_message(void)
{
    static UINT message;
    if (!message)
        message = RegisterWindowMessageA("MagicMayhem.Probe.BackgroundMouse.v1");
    return message;
}
#endif
#endif
