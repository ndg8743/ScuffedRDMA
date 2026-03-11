import { Cpu, Circle } from 'lucide-react';

export default function Header({ health }) {
  const modelOk = health?.model?.healthy;

  return (
    <header className="h-11 bg-ide-surface border-b border-ide-border flex items-center justify-between px-4 shrink-0 select-none">
      <div className="flex items-center gap-2.5">
        <Cpu size={18} className="text-ide-accent" />
        <span className="text-sm font-semibold tracking-wide text-ide-text">
          RISVLLM
        </span>
        <span className="text-[10px] font-medium text-ide-textDim bg-ide-bg px-1.5 py-0.5 rounded">
          v1.0
        </span>
      </div>

      <div className="flex items-center gap-4 text-xs text-ide-textDim">
        <span>LLM4Decompile-22B-v2</span>
        <div className="flex items-center gap-1.5">
          <Circle
            size={8}
            fill={modelOk ? '#3fb950' : modelOk === false ? '#f85149' : '#d29922'}
            className={modelOk ? 'text-ide-green' : modelOk === false ? 'text-ide-red' : 'text-ide-orange'}
          />
          <span>{modelOk ? 'Connected' : modelOk === false ? 'Offline' : 'Checking...'}</span>
        </div>
      </div>
    </header>
  );
}
