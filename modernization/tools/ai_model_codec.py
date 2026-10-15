"""Lossless native Brain model codec and recovered inference math (read-only)."""
import hashlib,math,struct
from pathlib import Path

def f32(value):return struct.unpack('<f',struct.pack('<f',value))[0]

def read_models(path):
    data=Path(path).read_bytes();pos=0;models=[]
    def read(fmt):
        nonlocal pos
        size=struct.calcsize('<'+fmt)
        if pos+size>len(data):raise ValueError('truncated model')
        v=struct.unpack_from('<'+fmt,data,pos);pos+=size;return v
    while pos<len(data):
        start=pos;action,dimension,count=read('III')
        if not(0<dimension<=1024 and 0<count<=32):raise ValueError('invalid model dimensions')
        classes=[]
        for _ in range(count):
            prior,n=read('fI')
            if n!=dimension:raise ValueError('inconsistent dimension')
            features=[]
            for _ in range(n):
                threshold,step,*bins=read('12f')
                features.append(dict(threshold=threshold,step=step,bins=bins))
            limit,=read('f');matrix=list(read('f'*(n*n)))
            classes.append(dict(prior=prior,features=features,limit=limit,matrix=matrix))
        models.append(dict(action_id=action,dimension=dimension,classes=classes,offset=start,end=pos))
    return dict(sha256=hashlib.sha256(data).hexdigest(),bytes=len(data),models=models)

def encode_models(decoded):
    parts=[]
    def put(fmt,*v):parts.append(struct.pack('<'+fmt,*v))
    for model in decoded['models']:
        n=model['dimension'];put('III',model['action_id'],n,len(model['classes']))
        for c in model['classes']:
            put('fI',c['prior'],n)
            for f in c['features']:put('12f',f['threshold'],f['step'],*f['bins'])
            put('f',c['limit']);put('f'*(n*n),*c['matrix'])
    return b''.join(parts)

def score(model,vector,exponent_scale,cutoff,epsilon,bin_factor):
    n=model['dimension'];classes=model['classes']
    if len(vector)!=n:raise ValueError('wrong feature count')
    if sum(c['prior']>0 for c in classes)<2:return [f32(1/len(classes))]*len(classes)
    distances=[]
    for c in classes:
        z=[]
        for x,f in zip(vector,c['features']):
            index=math.trunc((x-f['threshold'])/f['step']*bin_factor)
            z.append(-c['limit'] if index<0 else c['limit'] if index>=10 else f['bins'][index])
        q=0.0
        for i in range(n):
            for j in range(n):q=f32(c['matrix'][i*n+j]*z[j]*z[i]+q)
        distances.append(q)
    minimum=min(distances)
    weights=[0.0 if (q-minimum)*exponent_scale>=cutoff else math.exp(-(q-minimum)*exponent_scale) for q in distances]
    total=epsilon+sum(weights)
    return [f32(f32(w)/total) for w in weights]
