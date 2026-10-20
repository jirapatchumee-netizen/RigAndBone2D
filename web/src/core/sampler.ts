import { Project } from '../types';

export function sampleProjectAtTime(project: Project, time: number): number[] {
  if (project.frames.length === 0) {
    return project.bones.map((b) => b.angle);
  }

  const sorted = [...project.frames].sort((a, b) => a.time - b.time);
  const first = sorted[0];
  const last = sorted[sorted.length - 1];

  let a = first;
  for (let i = 0; i < sorted.length; i++) {
    if (sorted[i].time <= time) a = sorted[i];
  }

  let b = last;
  for (let i = sorted.length - 1; i >= 0; i--) {
    if (sorted[i].time >= time) b = sorted[i];
  }

  const u = b.time > a.time ? (time - a.time) / (b.time - a.time) : 0;

  return project.bones.map((_, i) => {
    const angleA = a.angles[i] ?? 0;
    const angleB = b.angles[i] ?? 0;
    return angleA + (angleB - angleA) * u;
  });
}

export function applySampledAngles(project: Project, time: number): void {
  const angles = sampleProjectAtTime(project, time);
  for (let i = 0; i < project.bones.length; i++) {
    project.bones[i].angle = angles[i];
  }
}
