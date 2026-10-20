import { Project, Bone, Point, Rect, AffineMatrix } from '../types';

export function radians(degrees: number): number {
  return (degrees * Math.PI) / 180;
}

export function degrees(radians: number): number {
  return (radians * 180) / Math.PI;
}

export function identityMatrix(): AffineMatrix {
  return { m11: 1, m12: 0, m21: 0, m22: 1, tx: 0, ty: 0 };
}

export function transformPoint(m: AffineMatrix, p: Point): Point {
  return {
    x: m.m11 * p.x + m.m21 * p.y + m.tx,
    y: m.m12 * p.x + m.m22 * p.y + m.ty,
  };
}

export function invertMatrix(m: AffineMatrix): AffineMatrix {
  const det = m.m11 * m.m22 - m.m12 * m.m21;
  if (Math.abs(det) < 1e-8) return identityMatrix();
  const invDet = 1 / det;
  return {
    m11: m.m22 * invDet,
    m12: -m.m12 * invDet,
    m21: -m.m21 * invDet,
    m22: m.m11 * invDet,
    tx: (m.m21 * m.ty - m.m22 * m.tx) * invDet,
    ty: (m.m12 * m.tx - m.m11 * m.ty) * invDet,
  };
}

export function computeTransforms(project: Project): AffineMatrix[] {
  const result: AffineMatrix[] = [];
  for (let i = 0; i < project.bones.length; i++) {
    const b = project.bones[i];
    const p = (b.parent !== null && b.parent !== undefined && b.parent < i)
      ? result[b.parent]
      : identityMatrix();

    const rad = radians(b.angle);
    const c = Math.cos(rad);
    const s = Math.sin(rad);

    const origin = transformPoint(p, { x: b.x, y: b.y });

    const t: AffineMatrix = {
      m11: p.m11 * c + p.m21 * s,
      m12: p.m12 * c + p.m22 * s,
      m21: -p.m11 * s + p.m21 * c,
      m22: -p.m12 * s + p.m22 * c,
      tx: origin.x,
      ty: origin.y,
    };
    result.push(t);
  }
  return result;
}

export function getBoneImageRect(b: Bone): Rect {
  const px = b.pivotX ?? 0.5;
  const py = b.pivotY ?? 0.15;
  const ox = b.imageOffsetX ?? 0;
  const oy = b.imageOffsetY ?? 0;
  return {
    x: -b.width * px + ox,
    y: -b.length * py + oy,
    width: b.width,
    height: b.length,
  };
}

export function getDrawOrder(project: Project): number[] {
  return project.bones
    .map((_, i) => i)
    .sort((a, b) => {
      const la = project.bones[a].layer;
      const lb = project.bones[b].layer;
      return la === lb ? a - b : la - lb;
    });
}
