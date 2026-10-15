// Inspect identified font strings and global font objects in a hash-specific database.
// @category MagicMayhem
import ghidra.app.util.headless.HeadlessScript;
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.program.model.address.Address;
import ghidra.program.model.data.DataUtilities;
import ghidra.program.model.listing.Data;
import ghidra.program.model.listing.Function;
import ghidra.program.model.mem.Memory;
import ghidra.program.model.symbol.Reference;
import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.util.*;

public class InspectFonts extends HeadlessScript {
    @Override public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 1) throw new IllegalArgumentException("output directory");
        Path out = Paths.get(args[0]);
        Files.createDirectories(out);
        StringBuilder evidence = new StringBuilder();
        Set<Function> targets = new LinkedHashSet<>();
        Memory memory = currentProgram.getMemory();
        for (long va : new long[]{0x6b0400L, 0x656680L, 0x6df1c0L, 0x581ec0L,
                                  0x4a5ae0L, 0x4a58e0L, 0x4a88f0L, 0x4a30b0L}) {
            Address address = toAddr(va);
            evidence.append("TARGET ").append(address).append("\n");
            Function own = currentProgram.getFunctionManager().getFunctionContaining(address);
            if (own != null) targets.add(own);
            for (Reference ref : currentProgram.getReferenceManager().getReferencesTo(address)) {
                Function caller = currentProgram.getFunctionManager().getFunctionContaining(ref.getFromAddress());
                evidence.append("  ").append(ref.getFromAddress()).append(" ")
                        .append(caller == null ? "?" : caller.getEntryPoint()).append("\n");
                if (caller != null) targets.add(caller);
            }
        }
        for (Data data : currentProgram.getListing().getDefinedData(true)) {
            if (!data.hasStringValue()) continue;
            String value = String.valueOf(data.getValue());
            if (!value.toLowerCase().contains(".sft")) continue;
            evidence.append("STRING ").append(data.getAddress()).append(" ").append(value).append("\n");
            for (Reference ref : currentProgram.getReferenceManager().getReferencesTo(data.getAddress())) {
                Function caller = currentProgram.getFunctionManager().getFunctionContaining(ref.getFromAddress());
                evidence.append("  ").append(ref.getFromAddress()).append(" ")
                        .append(caller == null ? "?" : caller.getEntryPoint()).append("\n");
                if (caller != null) targets.add(caller);
            }
        }
        Files.writeString(out.resolve("font-references.txt"), evidence.toString(), StandardCharsets.UTF_8);
        DecompInterface decompiler = new DecompInterface();
        try {
            if (!decompiler.openProgram(currentProgram)) throw new IllegalStateException(decompiler.getLastMessage());
            int count = 0;
            for (Function function : targets) {
                if (++count > 45) break;
                DecompileResults result = decompiler.decompileFunction(function, 30, monitor);
                String body = result.decompileCompleted() && result.getDecompiledFunction() != null
                        ? result.getDecompiledFunction().getC() : String.valueOf(result.getErrorMessage());
                Files.writeString(out.resolve(function.getEntryPoint() + ".c"), body, StandardCharsets.UTF_8);
            }
        } finally { decompiler.dispose(); }
        println("Font references and " + Math.min(targets.size(), 45) + " provisional functions written to " + out);
    }
}
