import { Project, Bone, Point, Rect, AffineMatrix, RigAxis } from '../types';
import {
  computeTransforms,
  getBoneImageRect,
  getDrawOrder,
  transformPoint,
  invertMatrix,
  radians,
  degrees,
} from '../core/transforms';
import { renderCellToCanvas } from '../core/export';

export interface Viewport {
  width: number;
  height: number;
  scale: number;
  pan: Point;
}

export class StageRenderer {
  canvas: HTMLCanvasElement;
  ctx: CanvasRenderingContext2D;
  viewport: Viewport = { width: 800, height: 600, scale: 1.8, pan: { x: 0, y: 0 } };
  imageCache = new Map<string, HTMLImageElement>();
  showBones = true;
  moveImageMode = false;
  selectedBoneIndex = 0;

  constructor(canvas: HTMLCanvasElement) {
    this.canvas = canvas;
    const context = canvas.getContext('2d');
    if (!context) throw new Error('Cannot get 2D context');
    this.ctx = context;
  }

  resize(width: number, height: number) {
    const dpr = window.devicePixelRatio || 1;
    this.canvas.width = width * dpr;
    this.canvas.height = height * dpr;
    this.canvas.style.width = `${width}px`;
    this.canvas.style.height = `${height}px`;
    this.viewport.width = width;
    this.viewport.height = height;
    this.ctx.resetTransform();
    this.ctx.scale(dpr, dpr);
  }

  get center(): Point {
    return {
      x: this.viewport.width / 2 + this.viewport.pan.x,
      y: this.viewport.height / 2 + this.viewport.pan.y,
    };
  }

  worldToView(p: Point): Point {
    return {
      x: this.center.x + p.x * this.viewport.scale,
      y: this.center.y + p.y * this.viewport.scale,
    };
  }

  viewToWorld(p: Point): Point {
    return {
      x: (p.x - this.center.x) / this.viewport.scale,
      y: (p.y - this.center.y) / this.viewport.scale,
    };
  }

  zoomAt(factor: number, anchor: Point) {
    const worldAnchor = this.viewToWorld(anchor);
    const newScale = Math.max(0.1, Math.min(12, this.viewport.scale * factor));
    this.viewport.pan.x = anchor.x - this.viewport.width / 2 - worldAnchor.x * newScale;
    this.viewport.pan.y = anchor.y - this.viewport.height / 2 - worldAnchor.y * newScale;
    this.viewport.scale = newScale;
  }

  ensureImageLoaded(data: string, onLoaded?: () => void) {
    if (!this.imageCache.has(data)) {
      const img = new Image();
      img.src = data.startsWith('data:') ? data : `data:image/png;base64,${data}`;
      img.onload = () => {
        onLoaded?.();
      };
      this.imageCache.set(data, img);
    }
  }

  getGizmoOrigin(project: Project): Point | null {
    if (!this.showBones || this.moveImageMode || !project.bones[this.selectedBoneIndex]) {
      return null;
    }
    const ts = computeTransforms(project);
    const t = ts[this.selectedBoneIndex];
    return this.worldToView({ x: t.tx, y: t.ty });
  }

  hitTestGizmo(project: Project, p: Point): RigAxis | null {
    const origin = this.getGizmoOrigin(project);
    if (!origin) return null;

    // Free square in center: 12x12
    if (Math.abs(p.x - origin.x) <= 10 && Math.abs(p.y - origin.y) <= 10) {
      return 'free';
    }
    // X handle arrow: from origin.x+12 to +62, y around origin.y +- 10
    if (p.x >= origin.x + 10 && p.x <= origin.x + 65 && Math.abs(p.y - origin.y) <= 10) {
      return 'x';
    }
    // Y handle arrow: from origin.y+12 to +62, x around origin.x +- 10
    if (p.y >= origin.y + 10 && p.y <= origin.y + 65 && Math.abs(p.x - origin.x) <= 10) {
      return 'y';
    }
    return null;
  }

  draw(project: Project) {
    const { width, height } = this.viewport;
    const ctx = this.ctx;

    // Background: #0e131f (RGB 0.055, 0.075, 0.12)
    ctx.fillStyle = '#0e131f';
    ctx.fillRect(0, 0, width, height);

    // Subtle Grid (32px)
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.04)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    for (let x = 0; x <= width; x += 32) {
      ctx.moveTo(x, 0);
      ctx.lineTo(x, height);
    }
    for (let y = 0; y <= height; y += 32) {
      ctx.moveTo(0, y);
      ctx.lineTo(width, y);
    }
    ctx.stroke();

    // Ensure all bone images are requested
    for (const b of project.bones) {
      if (b.image) this.ensureImageLoaded(b.image, () => this.draw(project));
    }

    // Render Character
    renderCellToCanvas(
      ctx,
      project,
      this.center.x,
      this.center.y,
      this.viewport.scale,
      this.imageCache
    );

    const ts = computeTransforms(project);

    // Overlays: Bone segments and joints
    if (this.showBones) {
      for (let i = 0; i < project.bones.length; i++) {
        const b = project.bones[i];
        if (b.visible === false) continue;

        const a = transformPoint(ts[i], { x: 0, y: 0 });
        const z = transformPoint(ts[i], { x: 0, y: b.length });

        const viewA = this.worldToView(a);
        const viewZ = this.worldToView(z);

        const isSelected = i === this.selectedBoneIndex;

        // Bone line
        ctx.beginPath();
        ctx.moveTo(viewA.x, viewA.y);
        ctx.lineTo(viewZ.x, viewZ.y);
        ctx.lineWidth = isSelected ? 3 : 1.5;
        ctx.strokeStyle = isSelected ? '#ffd60a' : '#30b0c7';
        ctx.stroke();

        // Joint Pivot Dot
        ctx.beginPath();
        ctx.arc(viewA.x, viewA.y, isSelected ? 5 : 3.5, 0, Math.PI * 2);
        ctx.fillStyle = isSelected ? '#ffd60a' : '#2ac3de';
        ctx.fill();
        ctx.strokeStyle = 'rgba(0,0,0,0.5)';
        ctx.lineWidth = 1;
        ctx.stroke();
      }
    }

    // Move Image Mode outline
    if (this.moveImageMode && project.bones[this.selectedBoneIndex]?.image) {
      const b = project.bones[this.selectedBoneIndex];
      const t = ts[this.selectedBoneIndex];
      ctx.save();
      ctx.transform(
        this.viewport.scale * t.m11,
        this.viewport.scale * t.m12,
        this.viewport.scale * t.m21,
        this.viewport.scale * t.m22,
        this.center.x + this.viewport.scale * t.tx,
        this.center.y + this.viewport.scale * t.ty
      );
      const rect = getBoneImageRect(b);
      ctx.strokeStyle = '#ffd60a';
      ctx.lineWidth = 2 / this.viewport.scale;
      ctx.setLineDash([4, 4]);
      ctx.strokeRect(rect.x, rect.y, rect.width, rect.height);
      ctx.restore();
    }

    // Draw Gizmo
    this.drawGizmo(project);

    // Stage Help Text at bottom
    ctx.fillStyle = 'rgba(255,255,255,0.45)';
    ctx.font = '12px system-ui, -apple-system, sans-serif';
    const help = this.moveImageMode
      ? 'Drag artwork to adjust offset · Joint pivots stay fixed'
      : 'Drag bone to rotate · Shift+Drag or Gizmo arrows to move · Wheel to zoom · Space+Drag to pan';
    ctx.fillText(help, 20, height - 20);
  }

  drawGizmo(project: Project) {
    const origin = this.getGizmoOrigin(project);
    if (!origin) return;

    const ctx = this.ctx;

    // X axis (Red)
    ctx.strokeStyle = '#ff453a';
    ctx.fillStyle = '#ff453a';
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(origin.x, origin.y);
    ctx.lineTo(origin.x + 58, origin.y);
    ctx.stroke();
    // Arrowhead
    ctx.beginPath();
    ctx.moveTo(origin.x + 58, origin.y);
    ctx.lineTo(origin.x + 48, origin.y - 5);
    ctx.lineTo(origin.x + 48, origin.y + 5);
    ctx.closePath();
    ctx.fill();
    ctx.font = 'bold 11px sans-serif';
    ctx.fillText('X', origin.x + 64, origin.y + 4);

    // Y axis (Green)
    ctx.strokeStyle = '#30d158';
    ctx.fillStyle = '#30d158';
    ctx.beginPath();
    ctx.moveTo(origin.x, origin.y);
    ctx.lineTo(origin.x, origin.y + 58);
    ctx.stroke();
    // Arrowhead
    ctx.beginPath();
    ctx.moveTo(origin.x, origin.y + 58);
    ctx.lineTo(origin.x - 5, origin.y + 48);
    ctx.lineTo(origin.x + 5, origin.y + 48);
    ctx.closePath();
    ctx.fill();
    ctx.fillText('Y', origin.x - 4, origin.y + 72);

    // Free square center
    ctx.fillStyle = '#1e2433';
    ctx.fillRect(origin.x - 6, origin.y - 6, 12, 12);
    ctx.strokeStyle = '#ffffff';
    ctx.lineWidth = 1.5;
    ctx.strokeRect(origin.x - 6, origin.y - 6, 12, 12);
  }
}
