#ifndef MM_PRESENTATION_EPOCH_H
#define MM_PRESENTATION_EPOCH_H
/* A control-table change is not a completed primary redraw. */
typedef struct MmPresentationEpoch { int mode, ready; unsigned signature,pending,frame;int pending_mode; } MmPresentationEpoch;
static __inline int mm_epoch_hold(MmPresentationEpoch* e,int live) {
    return e->ready && e->mode!=live;
}
static __inline int mm_epoch_redraw(MmPresentationEpoch* e,int mode,unsigned signature,unsigned frame) {
    if(!e->ready){e->mode=mode;e->signature=signature;e->ready=1;return 1;}
    if(e->signature==signature && e->mode==mode)return 1;
    if(e->pending!=signature || e->pending_mode!=mode){
        e->pending=signature;e->pending_mode=mode;e->frame=frame;return 0;
    }
    if(frame==e->frame)return 0;
    e->mode=mode;e->signature=signature;return 1;
}
static __inline void mm_epoch_commit(MmPresentationEpoch* e,int mode) {
    e->mode=mode;e->ready=1;
}
#endif
