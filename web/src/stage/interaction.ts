import { StageRenderer } from './canvas';
import { Project, Point, RigAxis } from '../types';
import {
  computeTransforms,
  getBoneImageRect,
  getDrawOrder,
  transformPoint,
  invertMatrix,
  radians,
  degrees,
} from '../core/transforms';

export interface InteractionCallbacks {
  onProjectChange: () => void;
  onSelectBone: (index: number) => void;
  onRecordHistory: (desc: string) => void;
}

export class StageInteraction {
  renderer: StageRenderer;
  getProject: () => Project;
  callbacks: InteractionCallbacks;

  isDragging = false;
  dragStart: Point = { x: 0, y: 0 };
  panStart: Point | null = null;
  axisDrag: RigAxis | null = null;
  boneDragIndex: number | null = null;
  imageDragIndex: number | null = null;
  isSpacePressed = false;
  initialBoneAngle = 0;
  hasMutated = false;

  constructor(
    renderer: StageRenderer,
    getProject: () => Project,
    callbacks: InteractionCallbacks
  ) {
    this.renderer = renderer;
    this.getProject = getProject;
    this.callbacks = callbacks;
    this.bindEvents();
  }

  bindEvents() {
    const canvas = this.renderer.canvas;

    window.addEventListener('keydown', (e) => {
      if (e.code === 'Space' && (e.target as HTMLElement).tagName !== 'INPUT') {
        this.isSpacePressed = true;
        canvas.style.cursor = 'grab';
      }
    });

    window.addEventListener('keyup', (e) => {
      if (e.code === 'Space') {
        this.isSpacePressed = false;
        canvas.style.cursor = 'default';
      }
    });

    canvas.addEventListener('wheel', (e) => {
      e.preventDefault();
      const rect = canvas.getBoundingClientRect();
      const anchor: Point = { x: e.clientX - rect.left, y: e.clientY - rect.top };
      const factor = e.deltaY < 0 ? 1.15 : 0.85;
      this.renderer.zoomAt(factor, anchor);
      this.callbacks.onProjectChange();
    }, { passive: false });

    canvas.addEventListener('pointerdown', (e) => {
      const rect = canvas.getBoundingClientRect();
      const p: Point = { x: e.clientX - rect.left, y: e.clientY - rect.top };
      this.dragStart = p;
      this.hasMutated = false;

      // Middle click or Space+click = Pan
      if (e.button === 1 || this.isSpacePressed) {
        this.panStart = p;
        canvas.style.cursor = 'grabbing';
        return;
      }

      if (e.button !== 0) return;

      const project = this.getProject();
      const gizmoHit = this.renderer.hitTestGizmo(project, p);

      if (gizmoHit) {
        this.axisDrag = gizmoHit;
        this.boneDragIndex = this.renderer.selectedBoneIndex;
        this.isDragging = true;
        return;
      }

      const ts = computeTransforms(project);

      // In Move Image mode: hit test artwork rects
      if (this.renderer.moveImageMode) {
        const worldP = this.renderer.viewToWorld(p);
        const drawOrderRev = [...getDrawOrder(project)].reverse();

        for (const idx of drawOrderRev) {
          const b = project.bones[idx];
          if (b.visible === false || !b.image) continue;
          const inv = invertMatrix(ts[idx]);
          const localP = transformPoint(inv, worldP);
          const r = getBoneImageRect(b);
          if (localP.x >= r.x && localP.x <= r.x + r.width && localP.y >= r.y && localP.y <= r.y + r.height) {
            this.renderer.selectedBoneIndex = idx;
            this.imageDragIndex = idx;
            this.isDragging = true;
            this.callbacks.onSelectBone(idx);
            return;
          }
        }
        return;
      }

      // Hit test bones (find closest bone segment to click)
      const worldP = this.renderer.viewToWorld(p);
      let closestIdx = -1;
      let minDistance = 35 / this.renderer.viewport.scale;

      for (let i = 0; i < project.bones.length; i++) {
        const b = project.bones[i];
        if (b.visible === false) continue;
        const a = transformPoint(ts[i], { x: 0, y: 0 });
        const z = transformPoint(ts[i], { x: 0, y: b.length });

        const dx = z.x - a.x;
        const dy = z.y - a.y;
        const lenSq = dx * dx + dy * dy;
        const u = Math.max(0, Math.min(1, ((worldP.x - a.x) * dx + (worldP.y - a.y) * dy) / Math.max(1, lenSq)));
        const projX = a.x + u * dx;
        const projY = a.y + u * dy;
        const dist = Math.hypot(worldP.x - projX, worldP.y - projY);

        if (dist < minDistance) {
          minDistance = dist;
          closestIdx = i;
        }
      }

      if (closestIdx >= 0) {
        this.renderer.selectedBoneIndex = closestIdx;
        this.boneDragIndex = closestIdx;
        this.isDragging = true;
        this.callbacks.onSelectBone(closestIdx);
      }
    });

    canvas.addEventListener('pointermove', (e) => {
      const rect = canvas.getBoundingClientRect();
      const p: Point = { x: e.clientX - rect.left, y: e.clientY - rect.top };

      // Pan handling
      if (this.panStart) {
        this.renderer.viewport.pan.x += p.x - this.panStart.x;
        this.renderer.viewport.pan.y += p.y - this.panStart.y;
        this.panStart = p;
        this.callbacks.onProjectChange();
        return;
      }

      if (!this.isDragging) return;

      const project = this.getProject();
      const selIdx = this.renderer.selectedBoneIndex;
      const b = project.bones[selIdx];
      if (!b) return;

      const ts = computeTransforms(project);
      const deltaX = (p.x - this.dragStart.x) / this.renderer.viewport.scale;
      const deltaY = (p.y - this.dragStart.y) / this.renderer.viewport.scale;

      // Handle Axis / Attachment Dragging
      if (this.axisDrag || (this.boneDragIndex === selIdx && e.shiftKey)) {
        const axis = this.axisDrag || 'free';
        const parentAngle = b.parent !== null && b.parent !== undefined && b.parent < selIdx
          ? Math.atan2(ts[b.parent].m12, ts[b.parent].m11)
          : 0;

        const dx = axis === 'y' ? 0 : deltaX;
        const dy = axis === 'x' ? 0 : deltaY;

        b.x += dx * Math.cos(parentAngle) + dy * Math.sin(parentAngle);
        b.y += -dx * Math.sin(parentAngle) + dy * Math.cos(parentAngle);
        this.hasMutated = true;
        this.dragStart = p;
        this.callbacks.onProjectChange();
        return;
      }

      // Handle Move Image Mode
      if (this.renderer.moveImageMode && this.imageDragIndex === selIdx) {
        const t = ts[selIdx];
        const worldAngle = Math.atan2(t.m12, t.m11);
        b.imageOffsetX = (b.imageOffsetX ?? 0) + deltaX * Math.cos(worldAngle) + deltaY * Math.sin(worldAngle);
        b.imageOffsetY = (b.imageOffsetY ?? 0) - deltaX * Math.sin(worldAngle) + deltaY * Math.cos(worldAngle);
        this.hasMutated = true;
        this.dragStart = p;
        this.callbacks.onProjectChange();
        return;
      }

      // Handle Bone Rotation Drag
      if (this.boneDragIndex === selIdx) {
        const a = transformPoint(ts[selIdx], { x: 0, y: 0 });
        const worldP = this.renderer.viewToWorld(p);
        const globalDeg = degrees(Math.atan2(worldP.y - a.y, worldP.x - a.x)) - 90;

        const parentDeg = b.parent !== null && b.parent !== undefined && b.parent < selIdx
          ? degrees(Math.atan2(ts[b.parent].m12, ts[b.parent].m11))
          : 0;

        b.angle = Math.round((globalDeg - parentDeg) * 10) / 10;
        this.hasMutated = true;
        this.dragStart = p;
        this.callbacks.onProjectChange();
      }
    });

    const stopDrag = () => {
      if (this.panStart) {
        this.panStart = null;
        canvas.style.cursor = this.isSpacePressed ? 'grab' : 'default';
      }
      if (this.hasMutated) {
        this.callbacks.onRecordHistory('Modify Bone');
      }
      this.isDragging = false;
      this.axisDrag = null;
      this.boneDragIndex = null;
      this.imageDragIndex = null;
    };

    canvas.addEventListener('pointerup', stopDrag);
    canvas.addEventListener('pointerleave', stopDrag);
  }
}
