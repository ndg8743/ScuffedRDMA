import { useState, useEffect, useCallback } from 'react';
import { Cpu, Circle, Power, PowerOff, Loader2 } from 'lucide-react';
import { getModelStatus, loadModel, unloadModel } from '../lib/api';

export default function Header({ health }) {
  const modelOk = health?.model?.healthy;
  const [modelState, setModelState] = useState(null); // stopped | starting | running | unschedulable
  const [actionLoading, setActionLoading] = useState(false);

  const fetchModelStatus = useCallback(async () => {
    try {
      const status = await getModelStatus();
      setModelState(status.state);
    } catch {
      setModelState(null);
    }
  }, []);

  // Poll model status every 10s
  useEffect(() => {
    fetchModelStatus();
    const interval = setInterval(fetchModelStatus, 10000);
    return () => clearInterval(interval);
  }, [fetchModelStatus]);

  const handleLoad = async () => {
    setActionLoading(true);
    try {
      await loadModel();
      setModelState('starting');
    } catch {}
    setActionLoading(false);
  };

  const handleUnload = async () => {
    setActionLoading(true);
    try {
      await unloadModel();
      setModelState('stopped');
    } catch {}
    setActionLoading(false);
  };

  const stateLabel =
    modelState === 'running' ? 'Connected' :
    modelState === 'starting' ? 'Loading...' :
    modelState === 'unschedulable' ? 'No GPU' :
    modelState === 'stopped' ? 'Stopped' :
    modelOk ? 'Connected' :
    modelOk === false ? 'Offline' : 'Checking...';

  const stateColor =
    modelState === 'running' || modelOk ? '#3fb950' :
    modelState === 'starting' ? '#d29922' :
    modelState === 'unschedulable' ? '#f85149' :
    modelState === 'stopped' ? '#8b949e' :
    modelOk === false ? '#f85149' : '#d29922';

  const showLoadBtn = modelState === 'stopped' || (modelState === null && modelOk === false);
  const showUnloadBtn = modelState === 'running' || (modelState === null && modelOk === true);
  const isStarting = modelState === 'starting' || modelState === 'unschedulable';

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

      <div className="flex items-center gap-3 text-xs text-ide-textDim">
        <span className="hidden sm:inline">LLM4Decompile-22B-v2</span>

        <div className="flex items-center gap-1.5">
          <Circle size={8} fill={stateColor} style={{ color: stateColor }} />
          <span>{stateLabel}</span>
        </div>

        {actionLoading ? (
          <Loader2 size={14} className="animate-spin text-ide-accent" />
        ) : showLoadBtn ? (
          <button
            onClick={handleLoad}
            className="flex items-center gap-1 px-2 py-1 rounded bg-ide-green/20 text-ide-green hover:bg-ide-green/30 transition-colors text-[11px] font-medium"
            title="Start vLLM model server"
          >
            <Power size={12} />
            Load
          </button>
        ) : isStarting ? (
          <span className="flex items-center gap-1 px-2 py-1 rounded bg-ide-orange/20 text-ide-orange text-[11px] font-medium">
            <Loader2 size={12} className="animate-spin" />
            Starting
          </span>
        ) : showUnloadBtn ? (
          <button
            onClick={handleUnload}
            className="flex items-center gap-1 px-2 py-1 rounded bg-ide-red/10 text-ide-textDim hover:text-ide-red hover:bg-ide-red/20 transition-colors text-[11px] font-medium"
            title="Stop vLLM model server"
          >
            <PowerOff size={12} />
            Unload
          </button>
        ) : null}
      </div>
    </header>
  );
}
