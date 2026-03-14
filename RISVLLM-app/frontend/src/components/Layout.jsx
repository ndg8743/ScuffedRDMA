import { useState, useCallback, useEffect } from 'react';
import { Panel, PanelGroup, PanelResizeHandle } from 'react-resizable-panels';
import { Play, Loader2, Square } from 'lucide-react';
import Header from './Header';
import Sidebar from './Sidebar';
import EditorPanel from './EditorPanel';
import OutputPanel from './OutputPanel';
import DiffView from './DiffView';
import UploadWizard from './UploadWizard';
import EmulatorModal from './EmulatorModal';
import StatusBar from './StatusBar';
import { decompileStream } from '../lib/api';

function useIsMobile() {
  const [isMobile, setIsMobile] = useState(window.innerWidth < 768);
  useEffect(() => {
    const handler = () => setIsMobile(window.innerWidth < 768);
    window.addEventListener('resize', handler);
    return () => window.removeEventListener('resize', handler);
  }, []);
  return isMobile;
}

export default function Layout({ health }) {
  const [activeTab, setActiveTab] = useState('decompile');
  const [inputCode, setInputCode] = useState('');
  const [outputCode, setOutputCode] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [emulatorOpen, setEmulatorOpen] = useState(false);
  const [status, setStatus] = useState({});
  const [mobilePanel, setMobilePanel] = useState('input'); // 'input' | 'output'
  const isMobile = useIsMobile();

  const handleResult = useCallback((result, streaming) => {
    setOutputCode(result);
    setIsStreaming(streaming);
    if (isMobile) setMobilePanel('output');
  }, [isMobile]);

  const handleTabChange = (tab) => {
    if (tab === 'emulator') {
      setEmulatorOpen(true);
    } else {
      setActiveTab(tab);
    }
  };

  const [isRunning, setIsRunning] = useState(false);
  const [optLevel, setOptLevel] = useState('O0');
  const abortRef = { current: null };

  const handleRun = useCallback(async () => {
    if (!inputCode.trim() || isRunning) return;
    setIsRunning(true);
    setOutputCode('');
    setIsStreaming(true);
    setStatus({ inputType: 'pseudo', optimizationLevel: optLevel });
    if (isMobile) setMobilePanel('output');
    const startTime = Date.now();
    let fullOutput = '';
    try {
      await decompileStream(inputCode, { optimizationLevel: optLevel, inputType: 'pseudo' }, (chunk) => {
        fullOutput += chunk;
        setOutputCode(fullOutput);
      });
      setStatus({ inputType: 'pseudo', optimizationLevel: optLevel, latency: Date.now() - startTime, tokens: Math.round(fullOutput.length / 4) });
    } catch (err) {
      setOutputCode(`// Error: ${err.message}`);
    } finally {
      setIsRunning(false);
      setIsStreaming(false);
    }
  }, [inputCode, optLevel, isRunning, isMobile]);

  const panelDirection = isMobile ? 'vertical' : 'horizontal';
  const resizeHandleClass = isMobile
    ? 'h-[3px] bg-ide-border hover:bg-ide-accent transition-colors cursor-row-resize'
    : 'w-[3px] bg-ide-border hover:bg-ide-accent transition-colors cursor-col-resize';

  return (
    <div className="h-screen w-screen flex flex-col overflow-hidden">
      <Header health={health} />

      <div className="flex-1 flex min-h-0">
        {/* Sidebar: bottom nav on mobile, left rail on desktop */}
        {!isMobile && <Sidebar activeTab={activeTab} onTabChange={handleTabChange} />}

        <main className="flex-1 min-w-0 min-h-0">
          {activeTab === 'decompile' && (
            <div className="h-full flex flex-col">
              {/* Run toolbar */}
              <div className="h-10 bg-ide-surface border-b border-ide-border flex items-center px-3 gap-3 shrink-0">
                <button
                  onClick={handleRun}
                  disabled={!inputCode.trim() || isRunning}
                  className={`h-7 px-3 rounded-md text-xs font-semibold flex items-center gap-1.5 transition-all
                    ${isRunning
                      ? 'bg-ide-red/20 text-ide-red'
                      : 'bg-ide-green/90 text-black hover:bg-ide-green disabled:opacity-30 disabled:cursor-not-allowed'
                    }`}
                >
                  {isRunning ? (
                    <><Loader2 size={13} className="animate-spin" /> Running...</>
                  ) : (
                    <><Play size={13} fill="currentColor" /> Decompile</>
                  )}
                </button>
                <div className="flex items-center gap-1 bg-ide-bg rounded-md border border-ide-border overflow-hidden">
                  {['O0', 'O1', 'O2', 'O3'].map((level) => (
                    <button
                      key={level}
                      onClick={() => setOptLevel(level)}
                      className={`px-2 py-1 text-[10px] font-mono font-bold transition-colors
                        ${optLevel === level ? 'bg-ide-accent text-white' : 'text-ide-textDim hover:text-ide-text'}`}
                    >
                      -{level}
                    </button>
                  ))}
                </div>
                <span className="text-[10px] text-ide-textDim ml-auto hidden sm:block">
                  Paste pseudo-code on the left, click Decompile
                </span>
              </div>

              {isMobile ? (
                <>
                  <div className="h-9 bg-ide-surface border-b border-ide-border flex shrink-0">
                    <button
                      onClick={() => setMobilePanel('input')}
                      className={`flex-1 text-xs font-medium transition-colors ${mobilePanel === 'input' ? 'text-ide-accent border-b-2 border-ide-accent' : 'text-ide-textDim'}`}
                    >
                      Input
                    </button>
                    <button
                      onClick={() => setMobilePanel('output')}
                      className={`flex-1 text-xs font-medium transition-colors ${mobilePanel === 'output' ? 'text-ide-accent border-b-2 border-ide-accent' : 'text-ide-textDim'}`}
                    >
                      Output {isStreaming && '●'}
                    </button>
                  </div>
                  <div className="flex-1 min-h-0">
                    {mobilePanel === 'input' ? (
                      <EditorPanel value={inputCode} onChange={setInputCode} language="plaintext" readOnly={false} />
                    ) : (
                      <OutputPanel value={outputCode} isStreaming={isStreaming} />
                    )}
                  </div>
                </>
              ) : (
                <div className="flex-1 min-h-0">
                  <PanelGroup direction={panelDirection}>
                    <Panel defaultSize={50} minSize={25}>
                      <EditorPanel value={inputCode} onChange={setInputCode} language="plaintext" readOnly={false} />
                    </Panel>
                    <PanelResizeHandle className={resizeHandleClass} />
                    <Panel defaultSize={50} minSize={25}>
                      <OutputPanel value={outputCode} isStreaming={isStreaming} />
                    </Panel>
                  </PanelGroup>
                </div>
              )}
            </div>
          )}

          {activeTab === 'wizard' && (
            isMobile ? (
              <div className="h-full flex flex-col">
                <div className="h-9 bg-ide-surface border-b border-ide-border flex shrink-0">
                  <button
                    onClick={() => setMobilePanel('input')}
                    className={`flex-1 text-xs font-medium transition-colors ${mobilePanel === 'input' ? 'text-ide-accent border-b-2 border-ide-accent' : 'text-ide-textDim'}`}
                  >
                    Wizard
                  </button>
                  <button
                    onClick={() => setMobilePanel('output')}
                    className={`flex-1 text-xs font-medium transition-colors ${mobilePanel === 'output' ? 'text-ide-accent border-b-2 border-ide-accent' : 'text-ide-textDim'}`}
                  >
                    Output {isStreaming && '●'}
                  </button>
                </div>
                <div className="flex-1 min-h-0">
                  {mobilePanel === 'input' ? (
                    <UploadWizard onResult={handleResult} onInputChange={setInputCode} onStatusChange={setStatus} />
                  ) : (
                    <OutputPanel value={outputCode} isStreaming={isStreaming} />
                  )}
                </div>
              </div>
            ) : (
              <PanelGroup direction={panelDirection}>
                <Panel defaultSize={35} minSize={25}>
                  <UploadWizard onResult={handleResult} onInputChange={setInputCode} onStatusChange={setStatus} />
                </Panel>
                <PanelResizeHandle className={resizeHandleClass} />
                <Panel defaultSize={65} minSize={30}>
                  <OutputPanel value={outputCode} isStreaming={isStreaming} />
                </Panel>
              </PanelGroup>
            )
          )}

          {activeTab === 'diff' && (
            <DiffView original={inputCode} modified={outputCode} />
          )}
        </main>
      </div>

      {/* Mobile bottom nav */}
      {isMobile && (
        <div className="h-14 bg-ide-surface border-t border-ide-border shrink-0">
          <Sidebar activeTab={activeTab} onTabChange={handleTabChange} mobile />
        </div>
      )}

      <StatusBar status={status} />
      <EmulatorModal isOpen={emulatorOpen} onClose={() => setEmulatorOpen(false)} />
    </div>
  );
}
