import { Project, Bone, Frame } from './types';
import { createDefaultProject } from './core/defaults';
import { applySampledAngles } from './core/sampler';

export interface EditorSnapshot {
  project: string; // JSON
  selectedBone: number;
  time: number;
  desc: string;
}

export class AppState {
  project: Project = createDefaultProject();
  selectedBone = 0;
  currentTime = 0;
  isPlaying = false;
  showBones = true;
  moveImageMode = false;

  undoStack: EditorSnapshot[] = [];
  redoStack: EditorSnapshot[] = [];

  listeners = new Set<() => void>();

  constructor() {
    this.record('Initial');
  }

  subscribe(listener: () => void) {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  notify() {
    this.listeners.forEach((l) => l());
  }

  record(desc: string) {
    const snap: EditorSnapshot = {
      project: JSON.stringify(this.project),
      selectedBone: this.selectedBone,
      time: this.currentTime,
      desc,
    };
    this.undoStack.push(snap);
    if (this.undoStack.length > 100) this.undoStack.shift();
    this.redoStack = [];
    this.notify();
  }

  undo() {
    if (this.undoStack.length <= 1) return;
    const current = this.undoStack.pop()!;
    this.redoStack.push(current);
    const prev = this.undoStack[this.undoStack.length - 1];
    this.restore(prev);
  }

  redo() {
    if (this.redoStack.length === 0) return;
    const next = this.redoStack.pop()!;
    this.undoStack.push(next);
    this.restore(next);
  }

  restore(snap: EditorSnapshot) {
    this.project = JSON.parse(snap.project);
    this.selectedBone = snap.selectedBone;
    this.currentTime = snap.time;
    this.notify();
  }

  setTime(t: number) {
    this.currentTime = Math.max(0, Math.min(this.project.duration, t));
    applySampledAngles(this.project, this.currentTime);
    this.notify();
  }

  togglePlay() {
    this.isPlaying = !this.isPlaying;
    this.notify();
  }

  addKeyframe() {
    const existingIdx = this.project.frames.findIndex(
      (f) => Math.abs(f.time - this.currentTime) < 0.01
    );
    const angles = this.project.bones.map((b) => b.angle);

    if (existingIdx >= 0) {
      this.project.frames[existingIdx].angles = angles;
    } else {
      this.project.frames.push({
        time: Math.round(this.currentTime * 100) / 100,
        angles,
      });
      this.project.frames.sort((a, b) => a.time - b.time);
    }
    this.record('Add Keyframe');
  }

  deleteCurrentKeyframe() {
    const idx = this.project.frames.findIndex(
      (f) => Math.abs(f.time - this.currentTime) < 0.05
    );
    if (idx >= 0 && this.project.frames.length > 1) {
      this.project.frames.splice(idx, 1);
      this.record('Delete Keyframe');
    }
  }

  addChildBone() {
    const parentIdx = this.selectedBone;
    const parentBone = this.project.bones[parentIdx];
    const newIdx = this.project.bones.length;

    const newBone: Bone = {
      name: `Bone ${newIdx}`,
      parent: parentIdx,
      x: 0,
      y: parentBone ? parentBone.length : 40,
      length: 45,
      angle: 0,
      width: 20,
      layer: (parentBone?.layer ?? 0) + 1,
      color: [0.35, 0.65, 0.85],
      pivotX: 0.5,
      pivotY: 0.15,
      imageOffsetX: 0,
      imageOffsetY: 0,
    };

    this.project.bones.push(newBone);
    for (const frame of this.project.frames) {
      frame.angles.push(0);
    }
    this.selectedBone = newIdx;
    this.record('Add Child Bone');
  }

  deleteSelectedBone() {
    if (this.project.bones.length <= 1) {
      alert('Cannot delete the last remaining bone.');
      return;
    }
    const idx = this.selectedBone;
    const bone = this.project.bones[idx];

    // Check descendants
    const descendants: number[] = [];
    const findDescendants = (p: number) => {
      for (let i = 0; i < this.project.bones.length; i++) {
        if (this.project.bones[i].parent === p) {
          descendants.push(i);
          findDescendants(i);
        }
      }
    };
    findDescendants(idx);

    const toDelete = new Set([idx, ...descendants]);
    const confirmed = confirm(
      `Delete bone "${bone.name}" and ${descendants.length} descendant(s)?`
    );
    if (!confirmed) return;

    // Filter bones and re-index parent references
    const oldBones = this.project.bones;
    const newBones: Bone[] = [];
    const indexMap = new Map<number, number>();

    let nextNewIndex = 0;
    for (let i = 0; i < oldBones.length; i++) {
      if (!toDelete.has(i)) {
        indexMap.set(i, nextNewIndex++);
        newBones.push({ ...oldBones[i] });
      }
    }

    for (const b of newBones) {
      if (b.parent !== null && b.parent !== undefined) {
        b.parent = indexMap.has(b.parent) ? indexMap.get(b.parent)! : null;
      }
    }

    // Update keyframe angles
    for (const f of this.project.frames) {
      f.angles = f.angles.filter((_, i) => !toDelete.has(i));
    }

    this.project.bones = newBones;
    this.selectedBone = Math.max(0, Math.min(newBones.length - 1, idx));
    this.record('Delete Bone');
  }

  reorderLayers(fromIndex: number, toIndex: number) {
    if (fromIndex === toIndex) return;
    const bone = this.project.bones[fromIndex];
    const targetBone = this.project.bones[toIndex];
    if (!bone || !targetBone) return;

    const tempLayer = bone.layer;
    bone.layer = targetBone.layer;
    targetBone.layer = tempLayer;
    this.record('Reorder Layers');
  }
}
