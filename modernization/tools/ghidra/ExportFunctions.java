// Export bounded decompiler output and call relationships without changing the program.
// @category MagicMayhem
import ghidra.app.util.headless.HeadlessScript;
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionIterator;
import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.io.BufferedWriter;

public class ExportFunctions extends HeadlessScript {
    @Override public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 2) throw new IllegalArgumentException("output-directory max-functions");
        Path out = Paths.get(args[0]);
        int limit = Integer.parseInt(args[1]);
        if (limit < 1) throw new IllegalArgumentException("max-functions must be positive");
        Files.createDirectories(out.resolve("pseudocode"));
        DecompInterface decompiler = new DecompInterface();
        int exported = 0, failed = 0;
        try (BufferedWriter index = Files.newBufferedWriter(out.resolve("functions.tsv"), StandardCharsets.UTF_8);
             BufferedWriter calls = Files.newBufferedWriter(out.resolve("calls.tsv"), StandardCharsets.UTF_8)) {
            if (!decompiler.openProgram(currentProgram)) throw new IllegalStateException(decompiler.getLastMessage());
            index.write("entry\tname\tstatus\n");
            calls.write("caller\tcallee\n");
            FunctionIterator functions = currentProgram.getFunctionManager().getFunctions(true);
            while (functions.hasNext() && exported < limit) {
                monitor.checkCancelled();
                Function function = functions.next();
                if (function.isExternal()) continue;
                String entry = function.getEntryPoint().toString();
                DecompileResults result = decompiler.decompileFunction(function, 30, monitor);
                boolean ok = result.decompileCompleted() && result.getDecompiledFunction() != null;
                index.write(entry + "\t" + function.getName().replace('\t', ' ').replace('\n', ' ') + "\t" + (ok ? "ok" : "failed") + "\n");
                if (ok) {
                    Files.writeString(out.resolve("pseudocode").resolve(entry + ".c"),
                        "/* Ghidra pseudocode; not verified compilable source. */\n" + result.getDecompiledFunction().getC(), StandardCharsets.UTF_8);
                } else {
                    failed++;
                    Files.writeString(out.resolve("pseudocode").resolve(entry + ".error.txt"), String.valueOf(result.getErrorMessage()), StandardCharsets.UTF_8);
                }
                for (Function callee : function.getCalledFunctions(monitor)) {
                    calls.write(entry + "\t" + callee.getEntryPoint() + "\n");
                }
                exported++;
            }
        } finally { decompiler.dispose(); }
        boolean timedOut = analysisTimeoutOccurred();
        Files.writeString(out.resolve("export-complete.json"),
            "{\"exported\":" + exported + ",\"failed\":" + failed +
            ",\"total_functions\":" + currentProgram.getFunctionManager().getFunctionCount() +
            ",\"analysis_timed_out\":" + timedOut + ",\"max_functions\":" + limit + "}\n", StandardCharsets.UTF_8);
        println("Exported " + exported + " functions; failed=" + failed + "; analysis_timed_out=" + timedOut);
    }
}
