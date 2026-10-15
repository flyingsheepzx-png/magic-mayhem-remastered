#pragma once
// Shared pure policy. Keep installed logic cadence exactly; render is a reader.
namespace mm_movement {
struct Contribution {int amount,remainder;};
inline bool compensated(int speed,int logic_rate,int players,unsigned id){
    return logic_rate==30 && players<=1 && speed>0 && speed<=1000000 && id<4096;
}
inline Contribution contribution(int speed,int remainder,int logic_rate,int players,unsigned id,bool walltime){
    if(!compensated(speed,logic_rate,players,id))return {speed,remainder};
    int numerator=speed*(walltime?31:2)+remainder,denominator=walltime?50:3;
    return {numerator/denominator,numerator%denominator};
}
inline double replay_ticks(double elapsed_seconds,double measured_span,int logic_rate,bool continuous){
    // A continuous speed describes one logic update, not one presented frame.
    double ticks=continuous && logic_rate>0?elapsed_seconds*logic_rate:
        (measured_span>0?elapsed_seconds/measured_span:0);
    if(ticks<0)return 0;return ticks>.75?.75:ticks;
}
}
