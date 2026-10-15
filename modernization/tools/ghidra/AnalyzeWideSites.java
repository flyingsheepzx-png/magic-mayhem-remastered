// @category MagicMayhem
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.Function;
import java.nio.file.*;
public class AnalyzeWideSites extends GhidraScript {
 public void run() throws Exception {
  Path output=Paths.get(getScriptArgs()[0]); Files.createDirectories(output);
  DecompInterface d=new DecompInterface();d.openProgram(currentProgram);
  try {
   long[] sites={0x4b4400,0x4b4b00,0x4b4e00,0x54f600,0x5505a0,0x550630,0x5506a0,0x4c5ce0,0x4c3dc0,0x4c57a0,0x577800};
   for(long a:sites) {
    Function f=getFunctionContaining(toAddr(a)); if(f==null){println("Missing function: "+Long.toHexString(a));continue;}
    DecompileResults r=d.decompileFunction(f,60,monitor);
    if(r.decompileCompleted())Files.writeString(output.resolve(f.getEntryPoint()+".c"),r.getDecompiledFunction().getC());
   }
  }finally{d.dispose();}
 }
}
