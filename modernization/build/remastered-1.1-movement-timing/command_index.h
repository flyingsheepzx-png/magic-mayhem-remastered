#pragma once
#include <stdint.h>
#include <string.h>

// Frame-local lookup. Reverse insertion preserves the old first-tag-wins rule,
// including identical commands belonging to different actors. No heap storage.
template<int Capacity, int Buckets=16384> struct CommandIndex {
    int heads[Buckets],next[Capacity];
    uint32_t hashes[Capacity];
    static uint32_t hash(const void* command) {
        const unsigned char* p=(const unsigned char*)command;
        uint32_t h=2166136261u;
        for(int i=0;i<36;i++)h=(h^p[i])*16777619u;
        return h;
    }
    template<class T> void build(const T* tags,int count) {
        for(int i=0;i<Buckets;i++)heads[i]=-1;
        for(int i=count-1;i>=0;i--){
            uint32_t h=hash(&tags[i].command);int bucket=h&(Buckets-1);
            hashes[i]=h;next[i]=heads[bucket];heads[bucket]=i;
        }
    }
    template<class T> int find(const void* command,const T* tags) const {
        uint32_t h=hash(command);
        for(int i=heads[h&(Buckets-1)];i>=0;i=next[i])
            if(hashes[i]==h && !memcmp(command,&tags[i].command,36))return i;
        return -1;
    }
};
