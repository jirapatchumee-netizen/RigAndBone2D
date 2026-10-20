import { AppState } from '../state';
import { StageRenderer } from '../stage/canvas';

export function createInspector(
  state: AppState,
  renderer: StageRenderer,
  onToast: (msg: string) => void
): HTMLElement {
  const container = document.createElement('aside');
  container.className = 'right-inspector';

  container.innerHTML = `
    <div class="inspector-section">
      <div class="inspector-title">Bone Properties</div>
      
      <div class="prop-row">
        <label class="prop-label">Name</label>
        <input type="text" class="prop-input-text" id="prop-name" />
      </div>

      <div class="prop-row">
        <label class="prop-label">Parent Bone</label>
        <select class="prop-input-text" id="prop-parent"></select>
      </div>
    </div>

    <div class="inspector-section" id="sliders-section">
      <div class="inspector-title">Transform & Geometry</div>
      <!-- Sliders injected here -->
    </div>

    <div class="inspector-section">
      <div class="inspector-title">Artwork & Texture</div>
      <div style="display: flex; flex-direction: column; gap: 8px;">
        <button class="btn" id="btn-import-png" style="width: 100%;">
          📁 Import PNG Artwork
        </button>
        <input type="file" id="file-input-png" accept="image/png,image/jpeg,image/webp" style="display: none;" />

        <div class="button-grid">
          <button class="btn" id="btn-toggle-move-image">
            Move Image Mode
          </button>
          <button class="btn" id="btn-clear-image" style="color: var(--color-red);">
            Remove Image
          </button>
        </div>
      </div>
    </div>
  `;

  const inputName = container.querySelector('#prop-name') as HTMLInputElement;
  const selectParent = container.querySelector('#prop-parent') as HTMLSelectElement;
  const slidersSection = container.querySelector('#sliders-section') as HTMLElement;
  const btnImportPng = container.querySelector('#btn-import-png') as HTMLButtonElement;
  const fileInputPng = container.querySelector('#file-input-png') as HTMLInputElement;
  const btnMoveImage = container.querySelector('#btn-toggle-move-image') as HTMLButtonElement;
  const btnClearImage = container.querySelector('#btn-clear-image') as HTMLButtonElement;

  const sliderConfigs: {
    key: string;
    label: string;
    min: number;
    max: number;
    step: number;
    getValue: (b: any) => number;
    setValue: (b: any, val: number) => void;
  }[] = [
    {
      key: 'angle',
      label: 'Angle (°)',
      min: -180,
      max: 180,
      step: 0.5,
      getValue: (b) => Math.round(b.angle * 10) / 10,
      setValue: (b, v) => (b.angle = v),
    },
    {
      key: 'length',
      label: 'Length',
      min: 1,
      max: 300,
      step: 1,
      getValue: (b) => Math.round(b.length),
      setValue: (b, v) => (b.length = v),
    },
    {
      key: 'width',
      label: 'Width',
      min: 1,
      max: 200,
      step: 1,
      getValue: (b) => Math.round(b.width),
      setValue: (b, v) => (b.width = v),
    },
    {
      key: 'x',
      label: 'Attach X',
      min: -300,
      max: 300,
      step: 1,
      getValue: (b) => Math.round(b.x),
      setValue: (b, v) => (b.x = v),
    },
    {
      key: 'y',
      label: 'Attach Y',
      min: -300,
      max: 300,
      step: 1,
      getValue: (b) => Math.round(b.y),
      setValue: (b, v) => (b.y = v),
    },
    {
      key: 'pivotX',
      label: 'Pivot X',
      min: 0,
      max: 1,
      step: 0.01,
      getValue: (b) => Math.round((b.pivotX ?? 0.5) * 100) / 100,
      setValue: (b, v) => (b.pivotX = v),
    },
    {
      key: 'pivotY',
      label: 'Pivot Y',
      min: 0,
      max: 1,
      step: 0.01,
      getValue: (b) => Math.round((b.pivotY ?? 0.15) * 100) / 100,
      setValue: (b, v) => (b.pivotY = v),
    },
    {
      key: 'imageOffsetX',
      label: 'Image Offset X',
      min: -300,
      max: 300,
      step: 1,
      getValue: (b) => Math.round(b.imageOffsetX ?? 0),
      setValue: (b, v) => (b.imageOffsetX = v),
    },
    {
      key: 'imageOffsetY',
      label: 'Image Offset Y',
      min: -300,
      max: 300,
      step: 1,
      getValue: (b) => Math.round(b.imageOffsetY ?? 0),
      setValue: (b, v) => (b.imageOffsetY = v),
    },
  ];

  // Build slider elements
  const sliderElements = new Map<string, { num: HTMLInputElement; range: HTMLInputElement }>();
  sliderConfigs.forEach((cfg) => {
    const row = document.createElement('div');
    row.className = 'prop-row';
    row.innerHTML = `
      <div class="prop-row-header">
        <span class="prop-label">${cfg.label}</span>
        <input type="number" class="prop-input-number" min="${cfg.min}" max="${cfg.max}" step="${cfg.step}" />
      </div>
      <input type="range" class="prop-slider" min="${cfg.min}" max="${cfg.max}" step="${cfg.step}" />
    `;
    const num = row.querySelector('input[type="number"]') as HTMLInputElement;
    const range = row.querySelector('input[type="range"]') as HTMLInputElement;

    num.addEventListener('change', () => {
      const val = parseFloat(num.value);
      const b = state.project.bones[state.selectedBone];
      if (b && !isNaN(val)) {
        cfg.setValue(b, val);
        range.value = val.toString();
        state.record(`Change ${cfg.label}`);
      }
    });

    range.addEventListener('input', () => {
      const val = parseFloat(range.value);
      const b = state.project.bones[state.selectedBone];
      if (b) {
        cfg.setValue(b, val);
        num.value = val.toString();
        state.notify();
      }
    });

    range.addEventListener('change', () => {
      state.record(`Change ${cfg.label}`);
    });

    sliderElements.set(cfg.key, { num, range });
    slidersSection.appendChild(row);
  });

  inputName.addEventListener('change', () => {
    const b = state.project.bones[state.selectedBone];
    if (b && inputName.value.trim()) {
      b.name = inputName.value.trim();
      state.record('Rename Bone');
    }
  });

  selectParent.addEventListener('change', () => {
    const b = state.project.bones[state.selectedBone];
    if (!b) return;
    const val = selectParent.value;
    b.parent = val === 'none' ? null : parseInt(val, 10);
    state.record('Change Parent');
  });

  btnImportPng.addEventListener('click', () => fileInputPng.click());
  fileInputPng.addEventListener('change', (e) => {
    const file = (e.target as HTMLInputElement).files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (evt) => {
      const b = state.project.bones[state.selectedBone];
      if (b && evt.target?.result) {
        // Base64 without data prefix or with data prefix
        const base64 = evt.target.result as string;
        b.image = base64;
        renderer.ensureImageLoaded(base64);
        state.record('Import Artwork PNG');
        onToast(`Imported image to ${b.name}`);
      }
    };
    reader.readAsDataURL(file);
    fileInputPng.value = '';
  });

  btnMoveImage.addEventListener('click', () => {
    renderer.moveImageMode = !renderer.moveImageMode;
    state.moveImageMode = renderer.moveImageMode;
    btnMoveImage.className = `btn ${renderer.moveImageMode ? 'btn-active' : ''}`;
    state.notify();
  });

  btnClearImage.addEventListener('click', () => {
    const b = state.project.bones[state.selectedBone];
    if (b && b.image) {
      b.image = null;
      state.record('Remove Image');
      onToast('Image removed');
    }
  });

  function update() {
    const b = state.project.bones[state.selectedBone];
    if (!b) return;

    inputName.value = b.name;

    // Populate Parent Dropdown
    selectParent.innerHTML = '<option value="none">None (Root)</option>';
    state.project.bones.forEach((other, idx) => {
      if (idx < state.selectedBone) {
        // Parent must have smaller index to prevent cycle
        const opt = document.createElement('option');
        opt.value = idx.toString();
        opt.textContent = `${idx}: ${other.name}`;
        if (b.parent === idx) opt.selected = true;
        selectParent.appendChild(opt);
      }
    });

    // Update Slider Values
    sliderConfigs.forEach((cfg) => {
      const el = sliderElements.get(cfg.key);
      if (el) {
        const val = cfg.getValue(b);
        el.num.value = val.toString();
        el.range.value = val.toString();
      }
    });

    btnMoveImage.className = `btn ${renderer.moveImageMode ? 'btn-active' : ''}`;
    btnClearImage.disabled = !b.image;
  }

  state.subscribe(update);
  update();

  return container;
}
