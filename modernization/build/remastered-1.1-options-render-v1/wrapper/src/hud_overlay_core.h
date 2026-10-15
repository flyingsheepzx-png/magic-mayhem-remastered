#ifndef MM_HUD_OVERLAY_CORE_H
#define MM_HUD_OVERLAY_CORE_H
#include <stdint.h>
typedef struct MmHudTile {
    unsigned kind,w,h,anchors[24];
    const unsigned short *low,*high;
    const unsigned char* mask;
} MmHudTile;
/* All locations are logical HUD pixels; only destination pixels use 2x.
   Compare against original pixels to preserve labels, cooldowns and tooltips. */
static unsigned short mm_hud_tint(unsigned short c,int dim){
    unsigned r=c>>11,g=(c>>5)&63,b=c&31;
    if(dim==1){r>>=1;g>>=1;b>>=1;}
    if(dim==2){r=r*3/4;g=g*3/4;b=b*3/4;}
    return (unsigned short)((r<<11)|(g<<5)|b);
}
static int mm_hud_match(const MmHudTile* t,const unsigned char* src,int pitch,int x,int y,int dim){
    unsigned j;
    if(x<0 || y<0 || x+(int)t->w>1280 || y+(int)t->h>720)return 0;
    if(t->kind==3){
        unsigned hits=0,run=0,best=0;
        // Native main portrait is a horizontal alive/dead split representing
        // health. Identify a substantial contiguous strip, then paint only
        // source-equal pixels from each sheet half separately.
        for(j=0;j<24;j++){
            unsigned k=t->anchors[j];const unsigned short* row=(const unsigned short*)(src+(y+k/t->w)*pitch);
            hits+=row[x+k%t->w]==mm_hud_tint(t->low[k],dim);
        }
        if(hits<3)return 0;
        for(j=0;j<t->h;j++){
            unsigned i,opaque=0;int equal=1;const unsigned short* row=(const unsigned short*)(src+(y+j)*pitch);
            for(i=0;i<t->w;i++)if(t->mask[j*t->w+i]){opaque++;if(row[x+i]!=mm_hud_tint(t->low[j*t->w+i],dim)){equal=0;break;}}
            run=equal&&opaque>=24?run+1:0;if(run>best)best=run;
        }
        return best>=12;
    }
    for(j=0;j<24;j++){
        unsigned k=t->anchors[j];
        const unsigned short* row=(const unsigned short*)(src+(y+k/t->w)*pitch);
        if(row[x+k%t->w]!=mm_hud_tint(t->low[k],dim))return 0;
    }
    // Similar spells can share border samples. Confirm the complete opaque
    // template before selecting artwork; obscured icons fall back natively.
    for(j=0;j<t->h;j++){
        unsigned i;const unsigned short* row=(const unsigned short*)(src+(y+j)*pitch);
        for(i=0;i<t->w;i++){
            unsigned k=j*t->w+i;
            if(t->mask[k] && row[x+i]!=mm_hud_tint(t->low[k],dim))return 0;
        }
    }
    return 1;
}
static unsigned mm_hud_paint(const MmHudTile* t,const unsigned char* src,int spitch,
                            unsigned char* dst,int dpitch,int x,int y,int dim){
    unsigned i,j,written=0;
    if(x<0 || y<0 || x+(int)t->w>1280 || y+(int)t->h>720)return 0;
    for(j=0;j<t->h;j++){
        const unsigned short* row=(const unsigned short*)(src+(y+j)*spitch);
        unsigned short* a=(unsigned short*)(dst+(y+j)*2*dpitch);
        unsigned short* b=(unsigned short*)(dst+((y+j)*2+1)*dpitch);
        if(t->kind==3){
            int equal=1;
            for(i=0;i<t->w;i++)if(t->mask[j*t->w+i] && row[x+i]!=mm_hud_tint(t->low[j*t->w+i],dim)){equal=0;break;}
            if(!equal)continue;
        }
        for(i=0;i<t->w;i++){
            unsigned k=j*t->w+i,hk=j*2*t->w*2+i*2,dx=(x+i)*2;
            if(!t->mask[k] || row[x+i]!=mm_hud_tint(t->low[k],dim))continue;
            a[dx]=mm_hud_tint(t->high[hk],dim);a[dx+1]=mm_hud_tint(t->high[hk+1],dim);
            b[dx]=mm_hud_tint(t->high[hk+t->w*2],dim);b[dx+1]=mm_hud_tint(t->high[hk+t->w*2+1],dim);
            written++;
        }
    }
    return written;
}
#endif
