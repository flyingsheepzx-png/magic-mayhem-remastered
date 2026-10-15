// Compile against the production header; compare with the prior linear lookup.
#include "command_index.h"
#include <stdio.h>
#include <stdlib.h>
#include <chrono>
struct Command {unsigned char bytes[36];};
struct Tag {Command command;int actor;};
static Tag tags[5000];static Command queries[12000];
static CommandIndex<5000> index_;
static CommandIndex<5000,1> collision_index;
static uint32_t seed=1234567;
static unsigned random_(){seed^=seed<<13;seed^=seed>>17;seed^=seed<<5;return seed;}
static int linear(const Command& command,int count){
    for(int i=0;i<count;i++)if(!memcmp(&command,&tags[i].command,36))return i;
    return -1;
}
static void require(bool ok){if(!ok){fprintf(stderr,"mismatch\n");exit(1);}}
static volatile unsigned checksum;
int main(){
    const int counts[]={0,1,73,5000,2,0};
    int checked=0;
    for(int count:counts){
        for(int i=0;i<count;i++){
            for(int b=0;b<36;b++)tags[i].command.bytes[b]=(unsigned char)random_();
            tags[i].actor=i;
            if(i && i%7==0)tags[i].command=tags[i/7].command;
        }
        index_.build(tags,count);collision_index.build(tags,count);
        for(int q=0;q<12000;q++){
            for(int b=0;b<36;b++)queries[q].bytes[b]=(unsigned char)random_();
            if(count && q%3)queries[q]=tags[random_()%count].command;
            if(count && q%11==0)queries[q].bytes[q%36]^=1;
            int expected=linear(queries[q],count);
            require(index_.find(&queries[q],tags)==expected);
            require(collision_index.find(&queries[q],tags)==expected);
            checked++;
        }
        if(count==5000){
            using namespace std::chrono;
            auto a=steady_clock::now();unsigned sum=0;
            for(int n=0;n<10;n++)for(int q=0;q<12000;q++)sum+=linear(queries[q],count)+1;
            checksum=sum;auto b=steady_clock::now();sum=0;
            for(int n=0;n<10;n++){
                index_.build(tags,count);
                for(int q=0;q<12000;q++)sum+=index_.find(&queries[q],tags)+1;
            }
            require(checksum==sum);checksum=sum;auto c=steady_clock::now();
            printf("Synthetic 5000 tags/12000 commands, 10 frames: linear %.3f ms, indexed %.3f ms\n",
                duration<double,std::milli>(b-a).count(),duration<double,std::milli>(c-b).count());
        }
    }
    printf("PASS: %d queries, normal and forced single-bucket collision index; duplicates, misses, byte differences, frame resets\n",checked);
}
