import { AppState } from '../state';
import { exportSpriteSheet } from '../core/export';
import { StageRenderer } from '../stage/canvas';
import { createDefaultProject } from '../core/defaults';

export function createHeader(
  state: AppState,
  renderer: StageRenderer,
  onToast: (msg: string) => void
): HTMLElement {
  const header = document.createElement('header');
  header.className = 'app-header';

  header.innerHTML = `
    <div class="brand">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
      </svg>
      <span>RigAndBone2D</span>
      <span class="badge">Web Edition</span>
    </div>

    <div class="header-actions">
      <select class="select-dropdown" id="preset-selector">
        <option value="" disabled selected>Load Preset...</option>
        <option value="default">Warrior (Basic Shapes)</option>
        <option value="baldr">Baldr Hero (22 Bones & Artwork)</option>
      </select>

      <button class="btn" id="btn-new" title="Create New Rig">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="12" y1="5" x2="12" y2="19"></line>
          <line x1="5" y1="12" x2="19" y2="12"></line>
        </svg>
        New
      </button>

      <button class="btn" id="btn-open" title="Open .rig2d JSON file">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>
        </svg>
        Open
      </button>
      <input type="file" id="file-input-project" accept=".rig2d,.json" style="display: none;" />

      <button class="btn" id="btn-save" title="Save .rig2d project to your disk">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path>
          <polyline points="17 21 17 13 7 13 7 21"></polyline>
          <polyline points="7 3 7 8 15 8"></polyline>
        </svg>
        Save
      </button>

      <button class="btn btn-primary" id="btn-export-sheet" title="Export 24-frame transparent PNG sprite sheet">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
          <circle cx="8.5" cy="8.5" r="1.5"></circle>
          <polyline points="21 15 16 10 5 21"></polyline>
        </svg>
        Export Sheet
      </button>

      <div style="width: 1px; height: 18px; background: var(--border-color); margin: 0 4px;"></div>

      <button class="btn" id="btn-undo" title="Undo (Cmd+Z)">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M3 7v6h6"></path>
          <path d="M21 17a9 9 0 0 0-9-9 9 9 0 0 0-6 2.3L3 13"></path>
        </svg>
      </button>

      <button class="btn" id="btn-redo" title="Redo (Cmd+Shift+Z)">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21 7v6h-6"></path>
          <path d="M3 17a9 9 0 0 1 9-9 9 9 0 0 1 6 2.3l3 2.7"></path>
        </svg>
      </button>
    </div>
  `;

  // Event Listeners
  const presetSelector = header.querySelector('#preset-selector') as HTMLSelectElement;
  presetSelector.addEventListener('change', async () => {
    const val = presetSelector.value;
    if (val === 'default') {
      state.project = createDefaultProject();
      state.selectedBone = 0;
      state.currentTime = 0;
      state.record('Load Default Demo');
      onToast('Loaded Warrior Demo');
    } else if (val === 'baldr') {
      try {
        onToast('Loading Baldr demo...');
        const res = await fetch('./presets/Baldr.rig2d');
        const json = await res.json();
        state.project = json;
        state.selectedBone = 0;
        state.currentTime = 0;
        state.record('Load Baldr Demo');
        onToast('Loaded Baldr Character Rig!');
      } catch (err) {
        alert('Failed to load Baldr preset: ' + err);
      }
    }
    presetSelector.value = '';
  });

  const btnNew = header.querySelector('#btn-new') as HTMLButtonElement;
  btnNew.addEventListener('click', () => {
    if (confirm('Create new project? Any unsaved edits will be lost.')) {
      state.project = createDefaultProject();
      state.selectedBone = 0;
      state.currentTime = 0;
      state.record('New Project');
      onToast('Created new project');
    }
  });

  const btnOpen = header.querySelector('#btn-open') as HTMLButtonElement;
  const fileInput = header.querySelector('#file-input-project') as HTMLInputElement;
  btnOpen.addEventListener('click', () => fileInput.click());
  fileInput.addEventListener('change', (e) => {
    const file = (e.target as HTMLInputElement).files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (evt) => {
      try {
        const json = JSON.parse(evt.target?.result as string);
        if (!json.bones || !Array.isArray(json.bones)) {
          throw new Error('Missing bones array');
        }
        state.project = json;
        state.selectedBone = 0;
        state.currentTime = 0;
        state.record(`Open ${file.name}`);
        onToast(`Loaded ${file.name}`);
      } catch (err) {
        alert('Invalid .rig2d file: ' + err);
      }
    };
    reader.readAsText(file);
    fileInput.value = '';
  });

  const btnSave = header.querySelector('#btn-save') as HTMLButtonElement;
  btnSave.addEventListener('click', () => {
    const jsonStr = JSON.stringify(state.project, null, 2);
    const blob = new Blob([jsonStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = (state.project.name || 'character').replace(/\s+/g, '_') + '.rig2d';
    a.click();
    URL.revokeObjectURL(url);
    onToast('Project saved!');
  });

  const btnExportSheet = header.querySelector('#btn-export-sheet') as HTMLButtonElement;
  btnExportSheet.addEventListener('click', async () => {
    try {
      onToast('Rendering 24-frame Sprite Sheet...');
      const blob = await exportSpriteSheet(state.project, renderer.imageCache);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = (state.project.name || 'character').replace(/\s+/g, '_') + '_sheet.png';
      a.click();
      URL.revokeObjectURL(url);
      onToast('Sprite Sheet exported!');
    } catch (err) {
      alert('Export failed: ' + err);
    }
  });

  const btnUndo = header.querySelector('#btn-undo') as HTMLButtonElement;
  btnUndo.addEventListener('click', () => state.undo());

  const btnRedo = header.querySelector('#btn-redo') as HTMLButtonElement;
  btnRedo.addEventListener('click', () => state.redo());

  // Global Keyboard Shortcuts
  window.addEventListener('keydown', (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'z') {
      if (e.shiftKey) {
        e.preventDefault();
        state.redo();
      } else {
        e.preventDefault();
        state.undo();
      }
    }
  });

  return header;
}
