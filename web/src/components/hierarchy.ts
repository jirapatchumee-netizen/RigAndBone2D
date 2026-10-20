import { AppState } from '../state';

export function createHierarchy(state: AppState): HTMLElement {
  const container = document.createElement('aside');
  container.className = 'left-sidebar';

  container.innerHTML = `
    <div class="sidebar-title">
      <span>Parts & Bones</span>
      <span style="font-size: 11px; opacity: 0.7;" id="bone-count">0</span>
    </div>
    <div class="sidebar-hint">Top = Front · Bottom = Back</div>
    <ul class="bones-list" id="bones-list"></ul>
    <div style="padding: 10px 14px; border-top: 1px solid var(--border-color); display: flex; gap: 6px;">
      <button class="btn" id="btn-add-bone" style="flex: 1;" title="Add Child Bone to Selected">
        + Add Child
      </button>
      <button class="btn" id="btn-del-bone" style="color: var(--color-red);" title="Delete Selected Bone">
        Delete
      </button>
    </div>
  `;

  const listEl = container.querySelector('#bones-list') as HTMLUListElement;
  const countEl = container.querySelector('#bone-count') as HTMLElement;
  const btnAdd = container.querySelector('#btn-add-bone') as HTMLButtonElement;
  const btnDel = container.querySelector('#btn-del-bone') as HTMLButtonElement;

  btnAdd.addEventListener('click', () => state.addChildBone());
  btnDel.addEventListener('click', () => state.deleteSelectedBone());

  function update() {
    countEl.textContent = `${state.project.bones.length}`;
    listEl.innerHTML = '';

    // Order items by drawOrder (layer descending: highest layer on top)
    const indicesByLayer = state.project.bones
      .map((_, i) => i)
      .sort((a, b) => state.project.bones[b].layer - state.project.bones[a].layer);

    for (const i of indicesByLayer) {
      const bone = state.project.bones[i];
      const li = document.createElement('li');
      li.className = `bone-item ${i === state.selectedBone ? 'selected' : ''}`;
      li.draggable = true;

      li.innerHTML = `
        <span class="bone-name">${bone.name}</span>
        <div style="display: flex; align-items: center; gap: 4px;">
          <span class="bone-badge">L${bone.layer}</span>
          <span style="opacity: ${bone.visible === false ? '0.3' : '1'}; cursor: pointer;" title="Toggle Visibility" class="vis-toggle">
            ${bone.visible === false ? '👁️‍🗨️' : '👁️'}
          </span>
        </div>
      `;

      li.addEventListener('click', (e) => {
        if ((e.target as HTMLElement).classList.contains('vis-toggle')) {
          bone.visible = bone.visible === false ? true : false;
          state.record('Toggle Visibility');
          return;
        }
        state.selectedBone = i;
        state.notify();
      });

      // Drag and Drop for layer reordering
      li.addEventListener('dragstart', (e) => {
        e.dataTransfer?.setData('text/plain', i.toString());
      });

      li.addEventListener('dragover', (e) => {
        e.preventDefault();
        li.style.borderTop = '2px solid var(--color-yellow)';
      });

      li.addEventListener('dragleave', () => {
        li.style.borderTop = '';
      });

      li.addEventListener('drop', (e) => {
        e.preventDefault();
        li.style.borderTop = '';
        const fromIdx = parseInt(e.dataTransfer?.getData('text/plain') || '-1', 10);
        if (fromIdx >= 0 && fromIdx !== i) {
          state.reorderLayers(fromIdx, i);
        }
      });

      listEl.appendChild(li);
    }
  }

  state.subscribe(update);
  update();

  return container;
}
