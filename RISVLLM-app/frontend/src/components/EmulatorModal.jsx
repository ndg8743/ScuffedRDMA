import { useState } from 'react';
import { X, Maximize2, Minimize2, MonitorPlay } from 'lucide-react';

const JSLINUX_URL = 'https://bellard.org/jslinux/vm.html?cpu=riscv64&url=buildroot-riscv64.cfg&mem=256';
const JSLINUX_GRAPHICAL = 'https://bellard.org/jslinux/vm.html?cpu=riscv64&url=buildroot-riscv64-xwin.cfg&graphic=1&mem=256';

export default function EmulatorModal({ isOpen, onClose }) {
  const [maximized, setMaximized] = useState(false);
  const [mode, setMode] = useState('console'); // 'console' | 'graphical'

  if (!isOpen) return null;

  const url = mode === 'graphical' ? JSLINUX_GRAPHICAL : JSLINUX_URL;

  return (
    <div className={`fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm`}>
      <div className={`bg-ide-surface border border-ide-border rounded-xl shadow-2xl flex flex-col overflow-hidden transition-all duration-200
        ${maximized ? 'w-full h-full rounded-none' : 'w-[85vw] h-[80vh]'}`}>

        {/* Title bar */}
        <div className="h-10 bg-ide-surface border-b border-ide-border flex items-center justify-between px-3 shrink-0 select-none">
          <div className="flex items-center gap-2">
            <MonitorPlay size={16} className="text-ide-accent" />
            <span className="text-xs font-semibold text-ide-text">RISC-V Emulator</span>
            <span className="text-[10px] text-ide-textDim bg-ide-bg px-1.5 py-0.5 rounded">
              TinyEMU · Buildroot Linux · riscv64
            </span>
          </div>
          <div className="flex items-center gap-1">
            {/* Mode toggle */}
            <div className="flex mr-3 bg-ide-bg rounded-md overflow-hidden border border-ide-border">
              <button
                onClick={() => setMode('console')}
                className={`px-2 py-1 text-[10px] transition-colors ${mode === 'console' ? 'bg-ide-accent text-white' : 'text-ide-textDim hover:text-ide-text'}`}
              >
                Console
              </button>
              <button
                onClick={() => setMode('graphical')}
                className={`px-2 py-1 text-[10px] transition-colors ${mode === 'graphical' ? 'bg-ide-accent text-white' : 'text-ide-textDim hover:text-ide-text'}`}
              >
                Graphical
              </button>
            </div>
            <button
              onClick={() => setMaximized(!maximized)}
              className="w-7 h-7 rounded flex items-center justify-center text-ide-textDim hover:text-ide-text hover:bg-ide-hover transition-colors"
            >
              {maximized ? <Minimize2 size={14} /> : <Maximize2 size={14} />}
            </button>
            <button
              onClick={onClose}
              className="w-7 h-7 rounded flex items-center justify-center text-ide-textDim hover:text-ide-red hover:bg-red-500/10 transition-colors"
            >
              <X size={14} />
            </button>
          </div>
        </div>

        {/* Emulator iframe */}
        <div className="flex-1 min-h-0 bg-black">
          <iframe
            src={url}
            className="w-full h-full border-0"
            title="RISC-V Emulator"
            sandbox="allow-scripts allow-same-origin allow-popups allow-downloads"
          />
        </div>

        {/* Footer hints */}
        <div className="h-7 bg-ide-surface border-t border-ide-border flex items-center px-3 text-[10px] text-ide-textDim shrink-0">
          <span>Tip: Use gcc to compile C code, then examine the binary with objdump</span>
          <span className="ml-auto">Powered by TinyEMU (Fabrice Bellard)</span>
        </div>
      </div>
    </div>
  );
}
