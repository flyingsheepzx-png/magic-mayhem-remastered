// Export identified functions from an existing, version-specific Ghidra database.
// @category MagicMayhem
import ghidra.app.util.headless.HeadlessScript;
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.program.model.listing.Function;
import java.nio.file.*;
import java.nio.charset.StandardCharsets;

public class ExportSelected extends HeadlessScript {
    @Override public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length < 2) throw new IllegalArgumentException("output-directory address...");
        Path out = Paths.get(args[0]);
        Files.createDirectories(out);
        DecompInterface decompiler = new DecompInterface();
        if (!decompiler.openProgram(currentProgram)) throw new IllegalStateException(decompiler.getLastMessage());
        try {
            for (int i = 1; i < args.length; i++) {
                monitor.checkCancelled();
                long address = Long.decode(args[i]);
                Function function = currentProgram.getFunctionManager().getFunctionContaining(
                    currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(address));
                if (function == null) {
                    var entryAddress = toAddr(address);
                    disassemble(entryAddress);
                    function = createFunction(entryAddress, null);
                }
                if (function == null) throw new IllegalArgumentException("No function at " + args[i]);
                DecompileResults result = decompiler.decompileFunction(function, 60, monitor);
                if (!result.decompileCompleted() || result.getDecompiledFunction() == null)
                    throw new IllegalStateException(args[i] + ": " + result.getErrorMessage());
                String entry = function.getEntryPoint().toString();
                Files.writeString(out.resolve(entry + ".c"),
                    "/* Ghidra pseudocode; verify disassembly before patching. */\n" +
                    result.getDecompiledFunction().getC(), StandardCharsets.UTF_8);
                println(args[i] + " -> " + entry);
            }
        } finally { decompiler.dispose(); }
    }
}
