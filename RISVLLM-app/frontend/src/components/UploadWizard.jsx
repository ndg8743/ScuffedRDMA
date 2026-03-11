import { useState, useRef } from 'react';
import { Upload, FileCode, ChevronRight, ChevronLeft, Loader2, AlertCircle } from 'lucide-react';
import { uploadFile, decompileStream } from '../lib/api';

const OPT_LEVELS = ['O0', 'O1', 'O2', 'O3'];

export default function UploadWizard({ onResult, onInputChange, onStatusChange }) {
  const [step, setStep] = useState(0);
  const [inputMode, setInputMode] = useState(null); // 'paste' | 'upload'
  const [code, setCode] = useState('');
  const [optLevel, setOptLevel] = useState('O0');
  const [uploading, setUploading] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState(null);
  const [fileName, setFileName] = useState('');
  const fileRef = useRef(null);

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      const result = await uploadFile(file);
      setCode(result.content);
      setFileName(result.filename);
      onInputChange?.(result.content);
      setStep(2);
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  };

  const handleDecompile = async () => {
    setProcessing(true);
    setError(null);
    onStatusChange?.({ inputType: inputMode, optimizationLevel: optLevel });
    const startTime = Date.now();
    let fullOutput = '';

    try {
      await decompileStream(code, {
        optimizationLevel: optLevel,
        inputType: inputMode === 'upload' ? 'assembly' : 'pseudo',
      }, (chunk) => {
        fullOutput += chunk;
        onResult?.(fullOutput, true);
      });
      onResult?.(fullOutput, false);
      onStatusChange?.({
        inputType: inputMode,
        optimizationLevel: optLevel,
        latency: Date.now() - startTime,
        tokens: Math.round(fullOutput.length / 4),
      });
    } catch (err) {
      setError(err.message);
    } finally {
      setProcessing(false);
    }
  };

  const steps = [
    // Step 0: Choose input method
    <div key="input-method" className="animate-fade-in space-y-4">
      <h2 className="text-lg font-semibold text-ide-text">Choose Input Method</h2>
      <p className="text-sm text-ide-textDim">How would you like to provide the code?</p>
      <div className="grid grid-cols-2 gap-3">
        <button
          onClick={() => { setInputMode('paste'); setStep(1); }}
          className="group p-6 rounded-xl border-2 border-ide-border hover:border-ide-accent bg-ide-bg hover:bg-ide-hover transition-all text-left"
        >
          <FileCode size={28} className="text-ide-accent mb-3" />
          <div className="font-medium text-ide-text text-sm">Paste Code</div>
          <div className="text-xs text-ide-textDim mt-1">
            Paste assembly or Ghidra pseudo-code
          </div>
        </button>
        <button
          onClick={() => { setInputMode('upload'); fileRef.current?.click(); }}
          className="group p-6 rounded-xl border-2 border-ide-border hover:border-ide-accent bg-ide-bg hover:bg-ide-hover transition-all text-left"
        >
          <Upload size={28} className="text-ide-purple mb-3" />
          <div className="font-medium text-ide-text text-sm">Upload Binary</div>
          <div className="text-xs text-ide-textDim mt-1">
            Upload an ELF/PE executable or .s file
          </div>
        </button>
      </div>
      <input
        ref={fileRef}
        type="file"
        className="hidden"
        onChange={handleFileUpload}
        accept=".bin,.elf,.exe,.o,.s,.asm,.pseudo,.c,.txt"
      />
      {uploading && (
        <div className="flex items-center gap-2 text-sm text-ide-accent">
          <Loader2 size={14} className="animate-spin" /> Processing file...
        </div>
      )}
    </div>,

    // Step 1: Paste code
    <div key="paste-code" className="animate-fade-in space-y-4 flex flex-col h-full">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-ide-text">Paste Code</h2>
        <button onClick={() => setStep(0)} className="text-xs text-ide-textDim hover:text-ide-text flex items-center gap-1">
          <ChevronLeft size={12} /> Back
        </button>
      </div>
      <textarea
        value={code}
        onChange={(e) => { setCode(e.target.value); onInputChange?.(e.target.value); }}
        placeholder={`# Paste assembly or Ghidra pseudo-code here...\n\nvoid FUN_00401000(void) {\n  int iVar1;\n  iVar1 = printf("Hello, World!\\n");\n  return;\n}`}
        className="flex-1 min-h-[200px] w-full bg-ide-bg border border-ide-border rounded-lg p-3 text-sm font-mono text-ide-text placeholder-ide-textDim/40 resize-none focus:outline-none focus:border-ide-accent transition-colors"
      />
      <button
        onClick={() => setStep(2)}
        disabled={!code.trim()}
        className="self-end px-4 py-2 bg-ide-accent text-white text-sm font-medium rounded-lg hover:bg-blue-500 disabled:opacity-30 disabled:cursor-not-allowed transition-all flex items-center gap-1.5"
      >
        Next <ChevronRight size={14} />
      </button>
    </div>,

    // Step 2: Optimization level
    <div key="opt-level" className="animate-fade-in space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-ide-text">Optimization Level</h2>
        <button onClick={() => setStep(inputMode === 'paste' ? 1 : 0)} className="text-xs text-ide-textDim hover:text-ide-text flex items-center gap-1">
          <ChevronLeft size={12} /> Back
        </button>
      </div>
      <p className="text-sm text-ide-textDim">
        What optimization level was used to compile the original binary?
      </p>
      <div className="grid grid-cols-4 gap-2">
        {OPT_LEVELS.map((level) => (
          <button
            key={level}
            onClick={() => setOptLevel(level)}
            className={`py-3 rounded-lg border-2 text-sm font-mono font-semibold transition-all
              ${optLevel === level
                ? 'border-ide-accent bg-ide-accentDim text-ide-accent'
                : 'border-ide-border text-ide-textDim hover:border-ide-accent/50 hover:text-ide-text'
              }`}
          >
            -{level}
          </button>
        ))}
      </div>
      <div className="text-xs text-ide-textDim space-y-1">
        <p><span className="text-ide-green">-O0</span>: No optimization (easiest to decompile)</p>
        <p><span className="text-ide-orange">-O1/-O2</span>: Standard optimizations</p>
        <p><span className="text-ide-red">-O3</span>: Aggressive (hardest to decompile)</p>
      </div>

      {fileName && (
        <div className="text-xs text-ide-textDim">
          File: <span className="text-ide-text">{fileName}</span> · {code.length.toLocaleString()} chars
        </div>
      )}

      <button
        onClick={() => setStep(3)}
        className="w-full py-2.5 bg-ide-accent text-white text-sm font-medium rounded-lg hover:bg-blue-500 transition-all flex items-center justify-center gap-1.5"
      >
        Review & Decompile <ChevronRight size={14} />
      </button>
    </div>,

    // Step 3: Review & Submit
    <div key="review" className="animate-fade-in space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-ide-text">Review</h2>
        <button onClick={() => setStep(2)} className="text-xs text-ide-textDim hover:text-ide-text flex items-center gap-1">
          <ChevronLeft size={12} /> Back
        </button>
      </div>

      <div className="space-y-2">
        <div className="flex justify-between text-sm">
          <span className="text-ide-textDim">Input</span>
          <span className="text-ide-text">{inputMode === 'upload' ? `File: ${fileName}` : 'Pasted code'}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-ide-textDim">Optimization</span>
          <span className="text-ide-orange font-mono">-{optLevel}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-ide-textDim">Input size</span>
          <span className="text-ide-text">{code.length.toLocaleString()} chars</span>
        </div>
      </div>

      <div className="bg-ide-bg border border-ide-border rounded-lg p-3 max-h-32 overflow-auto">
        <pre className="text-xs text-ide-textDim font-mono whitespace-pre-wrap">{code.slice(0, 500)}{code.length > 500 ? '\n...' : ''}</pre>
      </div>

      <button
        onClick={handleDecompile}
        disabled={processing}
        className="w-full py-3 bg-ide-green text-black text-sm font-bold rounded-lg hover:bg-green-400 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2"
      >
        {processing ? (
          <>
            <Loader2 size={16} className="animate-spin" />
            Decompiling...
          </>
        ) : (
          'Decompile'
        )}
      </button>
    </div>,
  ];

  return (
    <div className="h-full flex flex-col bg-ide-surface p-4 overflow-auto">
      {/* Step indicator */}
      <div className="flex items-center gap-1.5 mb-6 shrink-0">
        {['Input', 'Paste', 'Optimize', 'Run'].map((label, i) => (
          <div key={label} className="flex items-center gap-1.5">
            <div className={`w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold transition-all
              ${i <= step ? 'bg-ide-accent text-white' : 'bg-ide-border text-ide-textDim'}`}>
              {i + 1}
            </div>
            <span className={`text-[10px] ${i <= step ? 'text-ide-text' : 'text-ide-textDim'}`}>{label}</span>
            {i < 3 && <div className={`w-4 h-px ${i < step ? 'bg-ide-accent' : 'bg-ide-border'}`} />}
          </div>
        ))}
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg flex items-start gap-2 text-sm text-ide-red shrink-0">
          <AlertCircle size={16} className="mt-0.5 shrink-0" />
          <div>
            <p className="font-medium">Error</p>
            <p className="text-xs mt-0.5 text-ide-textDim">{error}</p>
          </div>
        </div>
      )}

      <div className="flex-1 min-h-0">
        {steps[step]}
      </div>
    </div>
  );
}
