import { DiffEditor } from '@monaco-editor/react';

export default function DiffView({ original, modified }) {
  return (
    <div className="h-full w-full flex flex-col bg-ide-bg">
      <div className="h-8 bg-ide-surface border-b border-ide-border flex items-center px-3 shrink-0">
        <span className="text-[11px] text-ide-textDim uppercase tracking-wider font-medium">
          Diff View — Assembly vs Decompiled C
        </span>
      </div>
      <div className="flex-1 min-h-0">
        {original || modified ? (
          <DiffEditor
            theme="vs-dark"
            original={original || '// No input'}
            modified={modified || '// No output'}
            originalLanguage="plaintext"
            modifiedLanguage="c"
            options={{
              fontSize: 13,
              fontFamily: '"JetBrains Mono", "Fira Code", monospace',
              minimap: { enabled: false },
              renderSideBySide: true,
              scrollBeyondLastLine: false,
              padding: { top: 12, bottom: 12 },
              automaticLayout: true,
              readOnly: true,
            }}
          />
        ) : (
          <div className="flex items-center justify-center h-full text-ide-textDim text-sm">
            Run a decompilation to see the diff view
          </div>
        )}
      </div>
    </div>
  );
}
