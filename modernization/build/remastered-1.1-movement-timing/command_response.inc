// Reuse validated physical redirection; never globally bypass native618 guard.
static bool response_walker(void* u){
 if(global(0x6e1f0c)!=0 || !field(u,4)||!field(u,0xe4)||
    field(u,0x618)!=1||field(u,0x5fc)!=2||
    field(u,0x104)||field(u,0x10c)||field(u,0xa0)||field(u,0x784)||field(u,0xde3)||
    *(unsigned char*)((char*)u+0x71c)||*(unsigned char*)((char*)u+0x723))return false;
 void* t=*(void**)((char*)u+0xac);
 return t&&field(t,8)==1&&field(t,12)>=1&&field(t,12)<=8&&field(t,0x44)==1;
}
static void commit_redirect_task(void* u,int task){
 // Physical redirect already owns its next cell and preserves world position.
 // Invoke the task callback at the normal movement boundary, not mid-segment.
 field(u,0x5ec)=task;field(u,0x5f0)=0;
 field(u,0x5f4)=task==3?0x50afa0:0x510010;field(u,0x5f8)=0;
 // Native50aa30's move-task exit removes the destination effect and queued
 // movement effects. Our physical redirect skips that task-exit callback.
 void* marker=*(void**)((char*)u+0x6e8);
 if(marker){((UnitFn)0x4943f0)(marker);field(u,0x6e8)=0;}
 void* tree=*(void**)((char*)u+0x8f9);
 if(tree && field(tree,8)){
  void* head=*(void**)((char*)tree+4);
  for(void* node=*(void**)head;node!=head;node=*(void**)node){
   if(field(node,8)==2 && field(node,40)){
    ((UnitFn)0x4943f0)(*(void**)((char*)node+40));field(node,40)=0;
   }
  }
 }
 // Recreate ordinary movement marker from the final task/goal; attacks omit it.
 if(field(u,0x68))((UnitFn)0x5120c0)(u);
}
static bool pursuit_to_move(void* u){
 if(!response_walker(u)||field(u,0x5ec)!=3||field(u,0x5f0)!=2)return false;
 field(u,0x5ec)=2;
 bool changed=on_order_impl(u);
 field(u,0x5ec)=3;
 if(changed)commit_redirect_task(u,2);
 return true; // The guarded attempt already ran, including native fallback.
}
static void __cdecl attack_response(void* u){
 // Shared native attack command for every army: same safety policy for player/AI.
 if(!response_walker(u)||(field(u,0x5ec)!=2&&field(u,0x5ec)!=3)||field(u,0x5f0)!=3)return;
 if(field(*(void**)((char*)u+0xac),0x34)!=0)return; // native ranged-pursuit branch
 int id=field(u,0x64c),capacity=global(0x6def5c);
 if(id<0||id>=capacity||capacity>1024)return;
 void* target=(char*)global(0x6def58)+id*0xe4b;
 if(!field(target,4)||!field(target,0xe4)||target==u)return;
 int gx=field(target,8),gy=field(target,12),gz=field(target,16);
 // Current melee neighborhood only; native pursuit handles ranged/flying targets
 // and long/unsafe approaches. Choose a free approach cell, never the enemy cell.
 if(field(target,0x104)||abs(gz-field(u,16))>1)return;
 int best=-1,bx=0,by=0;
 for(int dx=-1;dx<=1;++dx)for(int dy=-1;dy<=1;++dy){
  if(!dx&&!dy)continue;
  int x=gx+dx,y=gy+dy;
  if(!clear(u,x,y,gz))continue;
  int sx=x-field(u,8),sy=y-field(u,12),score=sx*sx+sy*sy;
  if(score && (best<0||score<best)){best=score;bx=x;by=y;}
 }
 if(best<0)return;
 int index=state_index(u);if(index<0)return;
 int goal[3];memcpy(goal,(char*)u+0x96b,12);int restart=field(u,0xb6f);
 memcpy((char*)u+0x96b,&bx,4);field(u,0x96f)=by;field(u,0x973)=gz;field(u,0xb6f)=1;
 int task=field(u,0x5ec);field(u,0x5ec)=2;
 load_state(u,index);
 bool changed=on_order_impl(u,false,true);
 field(u,0x5ec)=task;
 if(changed)commit_redirect_task(u,3);
 else {memcpy((char*)u+0x96b,goal,12);field(u,0xb6f)=restart;}
 save_state(index);
}
static unsigned state_native=0x50aa30;
__declspec(naked) static void attack_response_hook(){__asm{
 call dword ptr [state_native]
 pushfd
 pushad
 push esi
 call attack_response
 add esp,4
 popad
 popfd
 push 50aef7h
 ret
}}
