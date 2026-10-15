#pragma once
// Pure geometry: no engine addresses. Rendering adapters opt in separately.
#include <stdint.h>
struct MmUiViewport { int x,y,width,height,reference_width,reference_height; };
static inline MmUiViewport mm_ui_fit(int width,int height,int rw=800,int rh=600) {
    MmUiViewport v={0,0,0,0,rw,rh};
    if(width<=0 || height<=0 || rw<=0 || rh<=0)return v;
    if((int64_t)width*rh>(int64_t)height*rw){v.height=height;v.width=(int)((int64_t)height*rw/rh);}
    else {v.width=width;v.height=(int)((int64_t)width*rh/rw);}
    v.x=(width-v.width)/2;v.y=(height-v.height)/2;return v;
}
static inline int mm_ui_round(int value,int numerator,int denominator) {
    int64_t n=(int64_t)value*numerator;
    return (int)(n>=0?(n+denominator/2)/denominator:-((-n+denominator/2)/denominator));
}
static inline int mm_ui_project_x(MmUiViewport v,int x){return v.x+mm_ui_round(x,v.width,v.reference_width);}
static inline int mm_ui_project_y(MmUiViewport v,int y){return v.y+mm_ui_round(y,v.height,v.reference_height);}
static inline bool mm_ui_inverse(MmUiViewport v,int x,int y,int* rx,int* ry){
    if(v.width<=0 || v.height<=0 || x<v.x || y<v.y || x>=v.x+v.width || y>=v.y+v.height)return false;
    *rx=(int)((int64_t)(x-v.x)*v.reference_width/v.width);
    *ry=(int)((int64_t)(y-v.y)*v.reference_height/v.height);return true;
}

// Source rectangles remain unchanged; constrain only final destination origin.
static inline int mm_ui_clamp_origin(int origin,int extent,int minimum,int maximum){
    if(extent>maximum-minimum)return minimum;
    if(origin<minimum)return minimum;
    if(origin>maximum-extent)return maximum-extent;
    return origin;
}
static inline bool mm_ui_port_icon(int independent,int port_page,MmUiViewport v,int scale,int x,int y,int right,int bottom,int frame){
    return independent && port_page && frame>=0 && frame<234 &&
        scale>0 && x>=v.x && right<=v.x+v.width && y>=v.y && bottom<=v.y+v.height && right-x>=40*scale && bottom-y>=40*scale;
}
