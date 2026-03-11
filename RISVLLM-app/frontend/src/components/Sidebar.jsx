import { Code2, Upload, MonitorPlay, FileCode2 } from 'lucide-react';

const tabs = [
  { id: 'decompile', icon: Code2, label: 'Decompile' },
  { id: 'wizard', icon: Upload, label: 'Upload' },
  { id: 'emulator', icon: MonitorPlay, label: 'RISC-V' },
  { id: 'diff', icon: FileCode2, label: 'Diff' },
];

export default function Sidebar({ activeTab, onTabChange, mobile }) {
  if (mobile) {
    return (
      <nav className="flex items-center justify-around h-full px-2">
        {tabs.map(({ id, icon: Icon, label }) => (
          <button
            key={id}
            onClick={() => onTabChange(id)}
            className={`flex flex-col items-center gap-0.5 py-1 px-3 rounded-lg transition-all
              ${activeTab === id
                ? 'text-ide-accent'
                : 'text-ide-textDim'
              }`}
          >
            <Icon size={20} strokeWidth={1.5} />
            <span className="text-[9px] font-medium">{label}</span>
          </button>
        ))}
      </nav>
    );
  }

  return (
    <aside className="w-12 bg-ide-surface border-r border-ide-border flex flex-col items-center py-2 gap-1 shrink-0">
      {tabs.map(({ id, icon: Icon, label }) => (
        <button
          key={id}
          onClick={() => onTabChange(id)}
          title={label}
          className={`w-10 h-10 rounded-lg flex items-center justify-center transition-all duration-150
            ${activeTab === id
              ? 'bg-ide-accentDim text-ide-accent'
              : 'text-ide-textDim hover:text-ide-text hover:bg-ide-hover'
            }`}
        >
          <Icon size={20} strokeWidth={1.5} />
        </button>
      ))}
    </aside>
  );
}
