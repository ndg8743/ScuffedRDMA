import { Clock, Zap, FileCode } from 'lucide-react';

export default function StatusBar({ status }) {
  return (
    <footer className="h-6 bg-ide-surface border-t border-ide-border flex items-center justify-between px-3 text-[11px] text-ide-textDim shrink-0 select-none">
      <div className="flex items-center gap-4">
        <span className="flex items-center gap-1">
          <FileCode size={12} />
          {status.inputType || 'Ready'}
        </span>
        {status.optimizationLevel && (
          <span className="text-ide-orange">{status.optimizationLevel}</span>
        )}
      </div>

      <div className="flex items-center gap-4">
        {status.latency != null && (
          <span className="flex items-center gap-1">
            <Clock size={12} />
            {status.latency}ms
          </span>
        )}
        {status.tokens != null && (
          <span className="flex items-center gap-1">
            <Zap size={12} />
            {status.tokens} tokens
          </span>
        )}
        <span>Cerberus · 2x RTX 5090</span>
      </div>
    </footer>
  );
}
