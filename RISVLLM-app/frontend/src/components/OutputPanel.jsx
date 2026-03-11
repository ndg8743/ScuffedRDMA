import Editor from '@monaco-editor/react';

const EDITOR_OPTIONS = {
  fontSize: 13,
  fontFamily: '"JetBrains Mono", "Fira Code", monospace',
  fontLigatures: true,
  minimap: { enabled: false },
  lineNumbers: 'on',
  renderLineHighlight: 'none',
  scrollBeyondLastLine: false,
  padding: { top: 12, bottom: 12 },
  smoothScrolling: true,
  automaticLayout: true,
  wordWrap: 'on',
  readOnly: true,
};

export default function OutputPanel({ value, isStreaming }) {
  return (
    <div className="h-full w-full flex flex-col bg-ide-bg">
      <div className="h-8 bg-ide-surface border-b border-ide-border flex items-center px-3 shrink-0">
        <span className="text-[11px] text-ide-textDim uppercase tracking-wider font-medium">
          Output — Decompiled C
        </span>
        {isStreaming && (
          <span className="ml-2 text-[10px] text-ide-accent flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-ide-accent animate-pulse" />
            Streaming...
          </span>
        )}
        {value && (
          <button
            onClick={() => navigator.clipboard.writeText(value)}
            className="ml-auto text-[10px] text-ide-textDim hover:text-ide-text bg-ide-bg hover:bg-ide-hover px-2 py-0.5 rounded transition-colors"
          >
            Copy
          </button>
        )}
      </div>
      <div className="flex-1 min-h-0">
        {value ? (
          <Editor
            theme="vs-dark"
            language="c"
            value={value}
            options={EDITOR_OPTIONS}
            loading={
              <div className="flex items-center justify-center h-full text-ide-textDim text-sm">
                Loading editor...
              </div>
            }
          />
        ) : (
          <div className="flex items-center justify-center h-full text-ide-textDim text-sm">
            <div className="text-center space-y-2">
              <p className="text-base">No output yet</p>
              <p className="text-xs">Paste assembly code and click Decompile</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
