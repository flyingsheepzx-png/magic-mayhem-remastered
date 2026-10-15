#include "movement_timing.h"
#include <assert.h>
#include <math.h>
#include <initializer_list>
int main(){
    for(bool walltime:{false,true}){
        for(int rate:{20,30,40})for(int players:{0,1,2})for(unsigned id:{0u,7u,4095u,4096u}){
            long long sum=0,expected=0;int remainder=0;
            for(int i=0;i<10000;i++){
                int speed=(i%3==0?151:i%3==1?160:360);
                auto c=mm_movement::contribution(speed,remainder,rate,players,id,walltime);
                if(mm_movement::compensated(speed,rate,players,id)){
                    expected+=speed*(walltime?31:2);sum+=c.amount;remainder=c.remainder;
                    assert(sum*(walltime?50:3)+remainder==expected);
                }else{assert(c.amount==speed && c.remainder==remainder);}
            }
        }
    }
    for(int rate:{20,30,40})for(double span:{.016,.033,.05}){
        assert(fabs(mm_movement::replay_ticks(.01,span,rate,true)-.01*rate)<1e-12);
        assert(fabs(mm_movement::replay_ticks(.01,span,rate,false)-.01/span)<1e-12);
        assert(mm_movement::replay_ticks(1,span,rate,true)==.75);
        assert(mm_movement::replay_ticks(-1,span,rate,true)==0);
    }
    assert(mm_movement::replay_ticks(.01,0,0,false)==0);
}
