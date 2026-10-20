import { Project } from '../types';
import { computeTransforms, getBoneImageRect, getDrawOrder, radians } from './transforms';
import { sampleProjectAtTime } from './sampler';

export function renderCellToCanvas(
  ctx: CanvasRenderingContext2D,
  project: Project,
  centerX: number,
  centerY: number,
  scale: number,
  imageCache: Map<string, HTMLImageElement>
) {
  const ts = computeTransforms(project);
  const drawOrder = getDrawOrder(project);

  for (const i of drawOrder) {
    const b = project.bones[i];
    if (b.visible === false) continue;

    ctx.save();
    const t = ts[i];

    // Transform context to bone world origin and rotation
    ctx.transform(
      scale * t.m11,
      scale * t.m12,
      scale * t.m21,
      scale * t.m22,
      centerX + scale * t.tx,
      centerY + scale * t.ty
    );

    if (b.image) {
      const img = imageCache.get(b.image);
      const rect = getBoneImageRect(b);
      if (img && img.complete) {
        ctx.drawImage(img, rect.x, rect.y, rect.width, rect.height);
      }
    } else {
      // Draw default colored bone capsule
      const r = {
        x: -b.width / 2,
        y: -b.width * 0.12,
        width: b.width,
        height: b.length + b.width * 0.12,
      };
      const radius = b.width * 0.35;

      ctx.beginPath();
      ctx.roundRect(r.x, r.y, r.width, r.height, radius);
      ctx.fillStyle = `rgb(${Math.round(b.color[0] * 255)}, ${Math.round(b.color[1] * 255)}, ${Math.round(b.color[2] * 255)})`;
      ctx.fill();
      ctx.lineWidth = 2;
      ctx.strokeStyle = 'rgba(0,0,0,0.35)';
      ctx.stroke();
    }

    ctx.restore();
  }
}

export async function exportSpriteSheet(
  project: Project,
  imageCache: Map<string, HTMLImageElement>
): Promise<Blob> {
  const cell = 384;
  const cols = 6;
  const rows = 4;
  const totalFrames = 24;

  const canvas = document.createElement('canvas');
  canvas.width = cell * cols;
  canvas.height = cell * rows;
  const ctx = canvas.getContext('2d');
  if (!ctx) throw new Error('Could not get 2d context for export');

  ctx.clearRect(0, 0, canvas.width, canvas.height);

  for (let i = 0; i < totalFrames; i++) {
    const time = (i / totalFrames) * project.duration;
    const sampledAngles = sampleProjectAtTime(project, time);

    // Create a temporary cloned project pose
    const pose: Project = {
      ...project,
      bones: project.bones.map((b, idx) => ({ ...b, angle: sampledAngles[idx] ?? b.angle })),
    };

    const col = i % cols;
    const row = Math.floor(i / cols);
    const cellX = col * cell;
    const cellY = row * cell;

    ctx.save();
    ctx.beginPath();
    ctx.rect(cellX, cellY, cell, cell);
    ctx.clip();

    renderCellToCanvas(ctx, pose, cellX + cell / 2, cellY + cell / 2, 1, imageCache);
    ctx.restore();
  }

  return new Promise((resolve, reject) => {
    canvas.toBlob((blob) => {
      if (blob) resolve(blob);
      else reject(new Error('Failed to create PNG blob'));
    }, 'image/png');
  });
}
