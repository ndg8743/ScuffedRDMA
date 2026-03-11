import Editor from '@monaco-editor/react';

const EDITOR_OPTIONS = {
  fontSize: 13,
  fontFamily: '"JetBrains Mono", "Fira Code", monospace',
  fontLigatures: true,
  minimap: { enabled: false },
  lineNumbers: 'on',
  renderLineHighlight: 'line',
  scrollBeyondLastLine: false,
  padding: { top: 12, bottom: 12 },
  smoothScrolling: true,
  cursorBlinking: 'smooth',
  cursorSmoothCaretAnimation: 'on',
  bracketPairColorization: { enabled: true },
  automaticLayout: true,
  wordWrap: 'on',
};

export default function EditorPanel({ value, onChange, language, readOnly, placeholder }) {
  return (
    <div className="h-full w-full flex flex-col bg-ide-bg">
      <div className="h-8 bg-ide-surface border-b border-ide-border flex items-center px-3 shrink-0">
        <span className="text-[11px] text-ide-textDim uppercase tracking-wider font-medium">
          {readOnly ? 'Output — C Source' : 'Input — Assembly / Pseudo-code'}
        </span>
        <span className="ml-auto text-[10px] text-ide-textDim bg-ide-bg px-1.5 py-0.5 rounded">
          {language}
        </span>
      </div>
      <div className="flex-1 min-h-0">
        <Editor
          theme="vs-dark"
          language={language}
          value={value}
          onChange={readOnly ? undefined : onChange}
          options={{
            ...EDITOR_OPTIONS,
            readOnly,
          }}
          loading={
            <div className="flex items-center justify-center h-full text-ide-textDim text-sm">
              Loading editor...
            </div>
          }
        />
      </div>
    </div>
  );
}
