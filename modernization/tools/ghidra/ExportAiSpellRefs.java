// Identify native availability-matrix and effect-record candidate producers.
// @category MagicMayhem
import ghidra.app.util.headless.HeadlessScript;
import ghidra.program.model.listing.*;
import ghidra.program.model.scalar.Scalar;
import ghidra.program.model.address.Address;
import java.nio.file.*;
import java.util.*;
public class ExportAiSpellRefs extends HeadlessScript {
    public void run() throws Exception {
        Set<Long> targets=new HashSet<>(Arrays.asList(0x6b13edL,0x6b1250L,0x6b1270L,0x6b10bbL,0x19dL,0x17cL));
        StringBuilder out=new StringBuilder("value\tinstruction\tfunction\tdisassembly\n");
        InstructionIterator it=currentProgram.getListing().getInstructions(true);
        while(it.hasNext()) {
            monitor.checkCancelled();Instruction ins=it.next();
            for(int i=0;i<ins.getNumOperands();i++)for(Object obj:ins.getOpObjects(i)) {
                long x=obj instanceof Scalar?((Scalar)obj).getUnsignedValue():obj instanceof Address?((Address)obj).getOffset():-1;
                if(targets.contains(x) || (x>=0x6b13e0L && x<0x6b14f1L)) {
                    Function f=getFunctionContaining(ins.getAddress());
                    out.append(String.format("%x\t%s\t%s\t%s\n",x,ins.getAddress(),f==null?"-":f.getEntryPoint(),ins.toString()));
                }
            }
        }
        Files.writeString(Paths.get(getScriptArgs()[0]),out.toString());
    }
}
