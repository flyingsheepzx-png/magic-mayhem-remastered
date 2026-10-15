// Export a bounded direct-call closure from the existing identified engine.
// @category MagicMayhem
import ghidra.app.util.headless.HeadlessScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.Address;
import java.nio.file.*;
import java.util.*;

public class ExportAiClosure extends HeadlessScript {
    boolean ai(long x) { return (x>=0x407000 && x<0x46c000) || (x>=0x475000 && x<0x48b000); }
    public void run() throws Exception {
        String[] args=getScriptArgs();Path out=Paths.get(args[0]);Files.createDirectories(out);
        DecompInterface dc=new DecompInterface();dc.openProgram(currentProgram);
        ArrayDeque<Long> queue=new ArrayDeque<>();Set<Long> seen=new HashSet<>();
        for(int i=1;i<args.length;i++)queue.add(Long.decode(args[i]));
        StringBuilder index=new StringBuilder("requested\tentry\tstatus\n"),edges=new StringBuilder("caller\tcallee\n");
        try {
            while(!queue.isEmpty() && seen.size()<1800) {
                monitor.checkCancelled();long x=queue.remove();if(!seen.add(x))continue;
                Address a=toAddr(x);Function f=getFunctionContaining(a);
                if(f==null){disassemble(a);f=createFunction(a,null);}
                if(f==null){index.append(String.format("%08x\t-\tno-function\n",x));continue;}
                // Requested direct-call targets should be actual entries, not suffixes.
                long entry=f.getEntryPoint().getOffset();
                DecompileResults result=dc.decompileFunction(f,30,monitor);
                String status=result.decompileCompleted() && result.getDecompiledFunction()!=null?"ok":"failed";
                index.append(String.format("%08x\t%08x\t%s\n",x,entry,status));
                if(status.equals("ok"))Files.writeString(out.resolve(String.format("%08x.c",entry)),"/* Provisional pseudocode; boundary and ABI require disassembly. */\n"+result.getDecompiledFunction().getC());
                InstructionIterator it=currentProgram.getListing().getInstructions(f.getBody(),true);
                while(it.hasNext()) {
                    Instruction ins=it.next();if(!ins.getFlowType().isCall())continue;
                    for(Address target:ins.getFlows()) {
                        long y=target.getOffset();edges.append(String.format("%08x\t%08x\n",entry,y));
                        if(ai(y) && !seen.contains(y))queue.add(y);
                    }
                }
                if(seen.size()%20==0)println("AI closure exported "+seen.size()+", queued "+queue.size());
                Files.writeString(out.resolve("functions.tsv"),index.toString());
                Files.writeString(out.resolve("calls.tsv"),edges.toString());
            }
            Files.writeString(out.resolve("export-status.txt"),"visited="+seen.size()+" remaining="+queue.size()+"\n");
        } finally {dc.dispose();}
    }
}
