// Replan only a stationary native wait whose next cell has the native 0x10
// dynamic-obstacle bit. Unit congestion keeps the original wake/wait policy.
static bool dynamic_wait_detour(void* u,BlockedWait& s) {
    if(s.retry_cooldown>0){--s.retry_cooldown;return false;}
    if(field(u,0x66c)>6 ||
       !((BlockedFn)0x522f50)(u,s.next[0],s.next[1],s.next[2]))return false;
    // Failed searches are bounded to one per 28 subsequent waiting updates.
    s.retry_cooldown=28;
    int route[0x83];
    if(!local_route(u,s.goal[0],s.goal[1],s.goal[2],route) ||
       route[3]!=0 || route[4]<1 || route[4]>16 ||
       (route[5]==s.next[0] && route[6]==s.next[1] && route[7]==s.next[2]))return false;
    // No motion/reservation is active. Commit the complete validated route;
    // the native timer and action dispatcher start it on the next update.
    memcpy((char*)u+0x96b,route,sizeof(route));
    field(u,0xd03)=0;field(u,0x66c)=1;s.armed=false;
    log_event("dynamic_wait_detour",u,route[5],route[6]);
    return true;
}
