#pragma once
// Native-surface coordinates only. Output scaling belongs to the wrapper.
namespace mm_ui {
struct Rect {int left,top,right,bottom;};
struct Point {int x,y;};
inline int clamp_origin(int value,int extent,int limit) {
    if(value<0)return 0;
    return value+extent>limit ? limit-extent : value;
}
inline Point above_control(Rect target,Point tip,int width,int height,int screen_w,int screen_h) {
    Point p={(target.left+target.right)/2-tip.x,target.top-8-tip.y};
    p.x=clamp_origin(p.x,width,screen_w);p.y=clamp_origin(p.y,height,screen_h);
    return p;
}
}
