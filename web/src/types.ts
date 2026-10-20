export interface Bone {
  id?: string;
  visible?: boolean;
  name: string;
  parent?: number | null;
  x: number;
  y: number;
  length: number;
  angle: number;
  width: number;
  layer: number;
  color: [number, number, number]; // 0.0 to 1.0 RGB
  image?: string | null; // Base64 encoded PNG or data URL
  pivotX?: number; // default 0.5
  pivotY?: number; // default 0.15
  imageOffsetX?: number | null;
  imageOffsetY?: number | null;
}

export interface Frame {
  time: number;
  angles: number[];
  label?: string | null;
}

export interface Project {
  version: number;
  name?: string | null;
  bones: Bone[];
  frames: Frame[];
  duration: number;
}

export interface Point {
  x: number;
  y: number;
}

export interface Rect {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface AffineMatrix {
  m11: number;
  m12: number;
  m21: number;
  m22: number;
  tx: number;
  ty: number;
}

export type RigAxis = 'x' | 'y' | 'free';
