import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.Function;
import java.io.*;
public class FMVExport extends GhidraScript {
 public void run() throws Exception {
  DecompInterface d=new DecompInterface();d.openProgram(currentProgram);
  for(long v:new long[]{0x4696e0L,0x469830L,0x469a00L}){
   Function f=getFunctionAt(toAddr(v));if(f==null)f=createFunction(toAddr(v),null);
   DecompileResults r=d.decompileFunction(f,45,monitor);
   File out=new File(getScriptArgs()[0],Long.toHexString(v)+".c");
   try(PrintWriter w=new PrintWriter(out)){w.println(r.decompileCompleted()?r.getDecompiledFunction().getC():r.getErrorMessage());}
  }d.dispose();
 }
}
