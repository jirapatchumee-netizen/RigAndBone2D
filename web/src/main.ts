import './styles/main.css';
import { AppState } from './state';
import { StageRenderer } from './stage/canvas';
import { StageInteraction } from './stage/interaction';
import { createHeader } from './components/header';
import { createHierarchy } from './components/hierarchy';
import { createInspector } from './components/inspector';
import { createTimeline } from './components/timeline';

function showToast(message: string, duration = 3000) {
  const existing = document.querySelector('.toast');
  if (existing) existing.remove();

  const toast = document.createElement('div');
  toast.className = 'toast';
  toast.innerHTML = `
    <span>⚡</span>
    <span>${message}</span>
  `;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), duration);
}

function initApp() {
  const appContainer = document.getElementById('app');
  if (!appContainer) return;

  const state = new AppState();

  // Create Workspace DOM
  const workspace = document.createElement('div');
  workspace.className = 'workspace';

  const centerStage = document.createElement('main');
  centerStage.className = 'center-stage';

  const canvasContainer = document.createElement('div');
  canvasContainer.className = 'canvas-container';

  const canvas = document.createElement('canvas');
  canvas.id = 'stage-canvas';
  canvasContainer.appendChild(canvas);

  // Floating controls on stage (Zoom +, Zoom -, Fit, Toggle Bones)
  const floatingBar = document.createElement('div');
  floatingBar.className = 'stage-floating-bar';
  floatingBar.innerHTML = `
    <button class="btn" id="btn-zoom-in" title="Zoom In">+</button>
    <button class="btn" id="btn-zoom-out" title="Zoom Out">-</button>
    <button class="btn" id="btn-fit" title="Reset View / Fit Character">Fit</button>
    <button class="btn" id="btn-toggle-bones" title="Show/Hide Skeleton Lines">Bones</button>
  `;
  canvasContainer.appendChild(floatingBar);

  centerStage.appendChild(canvasContainer);

  const timeline = createTimeline(state);
  centerStage.appendChild(timeline);

  const renderer = new StageRenderer(canvas);

  const header = createHeader(state, renderer, showToast);
  const hierarchy = createHierarchy(state);
  const inspector = createInspector(state, renderer, showToast);

  workspace.appendChild(hierarchy);
  workspace.appendChild(centerStage);
  workspace.appendChild(inspector);

  appContainer.appendChild(header);
  appContainer.appendChild(workspace);

  // Handle Resize
  const handleResize = () => {
    renderer.resize(canvasContainer.clientWidth, canvasContainer.clientHeight);
    renderer.draw(state.project);
  };
  window.addEventListener('resize', handleResize);
  requestAnimationFrame(handleResize);

  // Sync state & renderer
  state.subscribe(() => {
    renderer.selectedBoneIndex = state.selectedBone;
    renderer.draw(state.project);
  });

  // Stage Interaction Handlers
  new StageInteraction(
    renderer,
    () => state.project,
    {
      onProjectChange: () => renderer.draw(state.project),
      onSelectBone: (idx) => {
        state.selectedBone = idx;
        state.notify();
      },
      onRecordHistory: (desc) => state.record(desc),
    }
  );

  // Floating Bar Button Handlers
  const btnZoomIn = floatingBar.querySelector('#btn-zoom-in') as HTMLButtonElement;
  const btnZoomOut = floatingBar.querySelector('#btn-zoom-out') as HTMLButtonElement;
  const btnFit = floatingBar.querySelector('#btn-fit') as HTMLButtonElement;
  const btnToggleBones = floatingBar.querySelector('#btn-toggle-bones') as HTMLButtonElement;

  btnZoomIn.addEventListener('click', () => {
    renderer.zoomAt(1.25, { x: renderer.viewport.width / 2, y: renderer.viewport.height / 2 });
    renderer.draw(state.project);
  });

  btnZoomOut.addEventListener('click', () => {
    renderer.zoomAt(0.8, { x: renderer.viewport.width / 2, y: renderer.viewport.height / 2 });
    renderer.draw(state.project);
  });

  btnFit.addEventListener('click', () => {
    renderer.viewport.pan = { x: 0, y: 0 };
    renderer.viewport.scale = 1.8;
    renderer.draw(state.project);
    showToast('Reset viewport');
  });

  btnToggleBones.addEventListener('click', () => {
    renderer.showBones = !renderer.showBones;
    state.showBones = renderer.showBones;
    btnToggleBones.className = `btn ${renderer.showBones ? 'btn-active' : ''}`;
    renderer.draw(state.project);
  });
  btnToggleBones.className = 'btn btn-active';

  // Initial draw
  renderer.draw(state.project);
}

document.addEventListener('DOMContentLoaded', initApp);
