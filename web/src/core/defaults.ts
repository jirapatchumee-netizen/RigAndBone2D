import { Project, Bone, Frame } from '../types';

export function createDefaultProject(): Project {
  function b(
    name: string,
    parent: number | null,
    x: number,
    y: number,
    length: number,
    angle: number,
    width: number,
    layer: number,
    color: [number, number, number]
  ): Bone {
    return {
      name,
      parent,
      x,
      y,
      length,
      angle,
      width,
      layer,
      color,
      pivotX: 0.5,
      pivotY: 0.15,
      imageOffsetX: 0,
      imageOffsetY: 0,
    };
  }

  const blue: [number, number, number] = [0.25, 0.43, 0.65];
  const skin: [number, number, number] = [0.96, 0.74, 0.46];
  const brown: [number, number, number] = [0.4, 0.26, 0.19];

  const bones: Bone[] = [
    b("Root / Hip", null, 0, 0, 8, 0, 22, 3, blue),
    b("Torso", 0, 0, 0, 85, 180, 64, 4, blue),
    b("Head", 1, 0, 85, 58, 0, 68, 8, skin),
    b("Back upper arm", 1, -30, 16, 48, 145, 23, 1, skin),
    b("Back forearm", 3, 0, 48, 44, -20, 20, 2, brown),
    b("Front upper arm", 1, 30, 16, 48, 215, 23, 6, skin),
    b("Front forearm", 5, 0, 48, 44, -35, 20, 7, brown),
    b("Sword", 6, 0, 44, 98, -100, 15, 9, [0.73, 0.86, 0.95]),
    b("Back thigh", 0, -18, 0, 55, 20, 28, 0, blue),
    b("Back shin", 8, 0, 55, 55, -15, 25, 1, brown),
    b("Front thigh", 0, 18, 0, 55, -20, 28, 5, blue),
    b("Front shin", 10, 0, 55, 55, 15, 25, 6, brown),
  ];

  const baseAngles = bones.map((bn) => bn.angle);
  const walkAngles = [...baseAngles];
  walkAngles[3] = 200;
  walkAngles[5] = 160;
  walkAngles[8] = -30;
  walkAngles[9] = 30;
  walkAngles[10] = 30;
  walkAngles[11] = -10;

  const frames: Frame[] = [
    { time: 0, angles: baseAngles, label: 'idle' },
    { time: 1, angles: walkAngles, label: 'step' },
    { time: 2, angles: baseAngles, label: 'loop' },
  ];

  return {
    version: 1,
    name: 'Warrior Demo',
    bones,
    frames,
    duration: 2.0,
  };
}
