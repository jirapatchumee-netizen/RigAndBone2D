import { AppState } from '../state';

export function createTimeline(state: AppState): HTMLElement {
  const container = document.createElement('section');
  container.className = 'timeline-panel';

  container.innerHTML = `
    <div class="timeline-controls">
      <div class="playback-controls">
        <button class="btn btn-primary" id="btn-play">
          ▶ Play
        </button>
        <span class="time-display" id="time-display">0.00s / 2.00s</span>
        
        <div style="display: flex; align-items: center; gap: 4px; font-size: 11px; color: var(--text-muted); margin-left: 10px;">
          <span>Duration:</span>
          <input type="number" id="input-duration" min="0.1" max="60" step="0.5" value="2" 
                 style="width: 50px; background: var(--bg-input); color: var(--text-main); border: 1px solid var(--border-color); border-radius: 4px; padding: 2px 4px; text-align: center;" />
          <span>s</span>
        </div>
      </div>

      <div style="display: flex; gap: 6px;">
        <button class="btn" id="btn-add-kf" title="Add keyframe at current time">
          + Keyframe
        </button>
        <button class="btn" id="btn-del-kf" title="Delete keyframe at current time" style="color: var(--color-red);">
          - Keyframe
        </button>
      </div>
    </div>

    <div class="timeline-track-container">
      <input type="range" class="timeline-slider" id="timeline-slider" min="0" max="2" step="0.01" value="0" />
      <div class="keyframe-ticks" id="keyframe-ticks"></div>
    </div>
  `;

  const btnPlay = container.querySelector('#btn-play') as HTMLButtonElement;
  const timeDisplay = container.querySelector('#time-display') as HTMLElement;
  const inputDuration = container.querySelector('#input-duration') as HTMLInputElement;
  const slider = container.querySelector('#timeline-slider') as HTMLInputElement;
  const ticksContainer = container.querySelector('#keyframe-ticks') as HTMLElement;
  const btnAddKf = container.querySelector('#btn-add-kf') as HTMLButtonElement;
  const btnDelKf = container.querySelector('#btn-del-kf') as HTMLButtonElement;

  let animFrameId: number | null = null;
  let lastTimestamp = 0;

  function loop(timestamp: number) {
    if (!lastTimestamp) lastTimestamp = timestamp;
    const dt = (timestamp - lastTimestamp) / 1000;
    lastTimestamp = timestamp;

    if (state.isPlaying) {
      let nextTime = state.currentTime + dt;
      if (nextTime > state.project.duration) {
        nextTime = nextTime % state.project.duration;
      }
      state.setTime(nextTime);
    }

    animFrameId = requestAnimationFrame(loop);
  }

  animFrameId = requestAnimationFrame(loop);

  btnPlay.addEventListener('click', () => {
    state.togglePlay();
  });

  slider.addEventListener('input', () => {
    state.isPlaying = false;
    state.setTime(parseFloat(slider.value));
  });

  inputDuration.addEventListener('change', () => {
    const val = parseFloat(inputDuration.value);
    if (!isNaN(val) && val > 0.1) {
      state.project.duration = val;
      state.record('Change Duration');
    }
  });

  btnAddKf.addEventListener('click', () => state.addKeyframe());
  btnDelKf.addEventListener('click', () => state.deleteCurrentKeyframe());

  // Spacebar shortcuts for play/pause
  window.addEventListener('keydown', (e) => {
    if (e.code === 'Space' && (e.target as HTMLElement).tagName !== 'INPUT') {
      e.preventDefault();
      state.togglePlay();
    }
  });

  function update() {
    btnPlay.innerHTML = state.isPlaying ? '⏸ Pause' : '▶ Play';
    btnPlay.className = `btn ${state.isPlaying ? 'btn-active' : 'btn-primary'}`;

    timeDisplay.textContent = `${state.currentTime.toFixed(2)}s / ${state.project.duration.toFixed(2)}s`;
    slider.max = state.project.duration.toString();
    slider.value = state.currentTime.toString();
    inputDuration.value = state.project.duration.toString();

    // Render Keyframe Diamond Ticks
    ticksContainer.innerHTML = '';
    state.project.frames.forEach((kf) => {
      const pct = (kf.time / state.project.duration) * 100;
      const tick = document.createElement('div');
      tick.className = 'keyframe-tick';
      tick.style.left = `${pct}%`;
      tick.title = `Keyframe at ${kf.time.toFixed(2)}s`;
      ticksContainer.appendChild(tick);
    });
  }

  state.subscribe(update);
  update();

  return container;
}
