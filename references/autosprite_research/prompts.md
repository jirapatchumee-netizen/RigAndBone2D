# Prompts & AI Generation Templates (Extracted from autosprite.app)

ไฟล์นี้รวบรวมชุดคำสั่ง (System Prompt & Instruction Templates) ที่สกัดออกมาจาก Binary ของ autosprite.app

---

## 1. การสร้างภาพนิ่ง 8 ทิศทาง (8-Directional Composite Stills)

ใช้สำหรับสั่งโมเดลสร้างภาพให้วาดตาราง 4×2 ที่มีครบทั้ง 8 มุมมองในภาพเดียว:

```text
Create exactly one composite image containing eight full-body views of the same character from the front-facing image. Use a borderless four-column, two-row grid with equal cells and no gaps. In reading order, the top row is front, front-right, right, back-right; the bottom row is back, back-left, left, front-left. Place exactly one centered character in each cell, with transparent space around it. Keep clothing, colors, proportions, and camera distance consistent. Return one image only; the app will crop and center the eight cells. Do not include labels, grid lines, or extra characters.
```

### การจัดวางในตาราง (4 Column × 2 Row Layout):

| Row \ Col | Col 0 | Col 1 | Col 2 | Col 3 |
|---|---|---|---|---|
| **Row 0 (บน)** | `front` (หันหน้าตรง) | `front-right` (เฉียงขวาหน้า) | `right` (หันข้างขวา) | `back-right` (เฉียงขวาหลัง) |
| **Row 1 (ล่าง)** | `back` (หันหลังตรง) | `back-left` (เฉียงซ้ายหลัง) | `left` (หันข้างซ้าย) | `front-left` (เฉียงซ้ายหน้า) |

---

## 2. การสร้างภาพนิ่งซ่อมเฉพาะมุม (Regenerate Single Still)

ใช้เมื่อมีบางทิศทางในตาราง 4×2 วาดออกมาไม่สวยงามหรือไม่สมบูรณ์:

```text
full-body still from the character image. Match the other directions' clothing, colors, proportions, camera distance, and transparent background. Do not change other directions.
```

---

## 3. การสร้างวิดีโอแอนิเมชันการเดิน (Walking Loop Video)

ใช้สำหรับส่งคำขอสร้างวิดีโอไปยังโมเดลวิดีโอ (เช่น `minimax/hailuo-3-max` ผ่าน OpenRouter):

```text
seamless walking loop from its approved still. The first frame already shows the entire character with generous empty space around the hood, hands, and feet; preserve that exact small full-body scale and center in every frame. Keep the hood and both feet fully inside the frame throughout the walk. Walk in place with no camera movement, zoom, reframing, extra objects, or background changes. Use a completely flat, uniform chroma-key background of exactly [CHROMA_COLOR]
```

*หมายเหตุ:* `[CHROMA_COLOR]` จะถูกแทนที่ด้วยรหัสสีที่ผู้ใช้เลือก:
* `Green · #00FF00`
* `Magenta · #FF00FF`
