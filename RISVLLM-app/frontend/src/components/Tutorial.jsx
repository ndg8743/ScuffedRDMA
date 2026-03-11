import { useState, useEffect } from 'react';
import { X, ChevronRight, ChevronLeft, Code2, Upload, MonitorPlay, FileCode2, Sparkles } from 'lucide-react';

const STORAGE_KEY = 'risvllm-tutorial-completed';

const STEPS = [
  {
    icon: Sparkles,
    title: 'Welcome to RISVLLM',
    description: 'A reverse engineering IDE powered by LLM4Decompile-22B — a 22-billion parameter AI model that converts assembly code back into readable C source code.',
    detail: 'Running on 2x NVIDIA RTX 5090 GPUs via the Cerberus compute node.',
    color: 'text-ide-accent',
  },
  {
    icon: Code2,
    title: 'Decompile',
    description: 'Paste assembly or Ghidra pseudo-code in the left editor panel. The AI model will generate decompiled C code in real-time on the right.',
    detail: 'Supports streaming output — watch the C code appear token by token.',
    color: 'text-ide-green',
  },
  {
    icon: Upload,
    title: 'Upload Wizard',
    description: 'Upload a compiled binary (.elf, .exe, .o) or paste code, choose the optimization level (O0–O3), review, and decompile in guided steps.',
    detail: 'Binaries are automatically disassembled with objdump before decompilation.',
    color: 'text-ide-purple',
  },
  {
    icon: MonitorPlay,
    title: 'RISC-V Emulator',
    description: 'Launch a full RISC-V Linux environment in your browser. Compile C code with GCC, run binaries, and examine them with objdump — all without leaving the IDE.',
    detail: 'Powered by TinyEMU — a lightweight RISC-V system emulator.',
    color: 'text-ide-orange',
  },
  {
    icon: FileCode2,
    title: 'Diff View',
    description: 'Compare your input assembly with the decompiled C output side-by-side in a unified diff view. Perfect for understanding what the model changed.',
    detail: 'Uses the Monaco diff editor — the same one in VS Code.',
    color: 'text-ide-accent',
  },
];

export default function Tutorial() {
  const [show, setShow] = useState(false);
  const [step, setStep] = useState(0);

  useEffect(() => {
    const completed = localStorage.getItem(STORAGE_KEY);
    if (!completed) setShow(true);
  }, []);

  const finish = () => {
    localStorage.setItem(STORAGE_KEY, 'true');
    setShow(false);
  };

  if (!show) return null;

  const current = STEPS[step];
  const Icon = current.icon;
  const isLast = step === STEPS.length - 1;

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/80 backdrop-blur-md">
      <div className="bg-ide-surface border border-ide-border rounded-2xl shadow-2xl w-full max-w-lg mx-4 overflow-hidden">
        {/* Progress bar */}
        <div className="h-1 bg-ide-border">
          <div
            className="h-full bg-ide-accent transition-all duration-300"
            style={{ width: `${((step + 1) / STEPS.length) * 100}%` }}
          />
        </div>

        <div className="p-8">
          {/* Icon */}
          <div className={`w-14 h-14 rounded-xl bg-ide-bg border border-ide-border flex items-center justify-center mb-5 ${current.color}`}>
            <Icon size={28} />
          </div>

          {/* Content */}
          <h2 className="text-xl font-bold text-ide-text mb-2">{current.title}</h2>
          <p className="text-sm text-ide-textDim leading-relaxed mb-3">{current.description}</p>
          <p className="text-xs text-ide-textDim/70 leading-relaxed">{current.detail}</p>

          {/* Step dots */}
          <div className="flex items-center justify-center gap-2 mt-6 mb-6">
            {STEPS.map((_, i) => (
              <button
                key={i}
                onClick={() => setStep(i)}
                className={`w-2 h-2 rounded-full transition-all ${i === step ? 'bg-ide-accent w-6' : 'bg-ide-border hover:bg-ide-textDim'}`}
              />
            ))}
          </div>

          {/* Navigation */}
          <div className="flex items-center justify-between">
            <button
              onClick={finish}
              className="text-xs text-ide-textDim hover:text-ide-text transition-colors"
            >
              Skip tutorial
            </button>
            <div className="flex items-center gap-2">
              {step > 0 && (
                <button
                  onClick={() => setStep(step - 1)}
                  className="px-3 py-1.5 text-sm text-ide-textDim hover:text-ide-text border border-ide-border rounded-lg hover:bg-ide-hover transition-all flex items-center gap-1"
                >
                  <ChevronLeft size={14} /> Back
                </button>
              )}
              <button
                onClick={isLast ? finish : () => setStep(step + 1)}
                className="px-4 py-1.5 text-sm font-medium bg-ide-accent text-white rounded-lg hover:bg-blue-500 transition-all flex items-center gap-1"
              >
                {isLast ? 'Get Started' : 'Next'} {!isLast && <ChevronRight size={14} />}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
