// Locate candidate AI field accesses throughout the identified native image.
// @category MagicMayhem
import ghidra.app.util.headless.HeadlessScript;
import ghidra.program.model.listing.*;
import ghidra.program.model.scalar.Scalar;
import java.nio.file.*;
import java.util.*;
public class ExportAiFieldRefs extends HeadlessScript {
    public void run() throws Exception {
        Set<Long> fields=new HashSet<>(Arrays.asList(0x2fL,0x33L,0x8e5L,0x922L,0x926L,0x92aL,0x936L,0x93aL,0x93eL,0x942L,0x946L,0x94aL,0x94eL,0x952L,0x956L));
        StringBuilder out=new StringBuilder("field\tinstruction\tfunction\tdisassembly\n");
        InstructionIterator it=currentProgram.getListing().getInstructions(true);
        while(it.hasNext()) {
            monitor.checkCancelled();Instruction ins=it.next();
            for(int i=0;i<ins.getNumOperands();i++) {
                if(!ins.getDefaultOperandRepresentation(i).contains("["))continue;
                for(Object obj:ins.getOpObjects(i))if(obj instanceof Scalar) {
                    long x=((Scalar)obj).getUnsignedValue();
                    if(fields.contains(x)) {
                        Function f=getFunctionContaining(ins.getAddress());
                        out.append(String.format("%x\t%s\t%s\t%s\n",x,ins.getAddress(),f==null?"-":f.getEntryPoint(),ins.toString()));
                    }
                }
            }
        }
        Files.writeString(Paths.get(getScriptArgs()[0]),out.toString());
    }
}
