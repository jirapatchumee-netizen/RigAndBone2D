# Demo 2 — High Priest Inquisitor / Morning Star combat

ตัวละครที่ 2 สร้างจาก sprite sheet ที่ผู้ใช้ให้ มี 17 กระดูกของตัวละคร/อาวุธ และ 5 กระดูกของหุ่นฝึก รวม 22 กระดูก คีย์เฟรม 13 จุด รอบแอนิเมชัน 3 วินาที

## จังหวะต่อสู้

- ตั้งการ์ดและเตรียมเหวี่ยง (0–0.95 วินาที)
- เหวี่ยงอาวุธและปะทะหุ่นฝึก (1–1.3 วินาที)
- โซ่สะบัดตามและหุ่นเอนรับแรง (1.3–1.85 วินาที)
- คืนท่าและกลับมาตั้งการ์ด (2–3 วินาที)

โซ่และแรงตอบสนองของหุ่นฝึกออกแบบด้วยคีย์เฟรม ไม่มีระบบฟิสิกส์หรือ collision simulation ในรุ่นนี้ ภาพตัวละครใช้ชิ้นต้นฉบับ ไม่ได้สร้างภาพแต่ละท่าด้วย AI

## เปิดใช้งาน

กด Open ในแอป แล้วเลือก `Inquisitor-combat.rig2d` จากนั้นกด Play / Pause หรือใช้คำสั่งจากโฟลเดอร์โปรเจกต์:

```sh
open -n dist/RigAndBone2D.app --args --project "$(pwd)/examples/inquisitor/Inquisitor-combat.rig2d" --play
```

ภาพทุกชิ้นฝังในไฟล์โปรเจกต์แล้ว

## ผลลัพธ์

- `Inquisitor-combat.rig2d`: โปรเจกต์ที่เล่นและแก้ต่อได้
- `Inquisitor-combat.gif`, `Inquisitor-combat.mp4`: แอนิเมชัน 3 วินาที, 20 fps, 60 เฟรมที่เรนเดอร์ผ่าน API จริง
- `Inquisitor-sheet.png`: sprite sheet โปร่งใส 24 เฟรม, 6 × 4 ช่อง, 384 × 384 พิกเซลต่อช่อง; ใช้ 8 fps เพื่อเล่นครบ 3 วินาที
- `Inquisitor-sheet.json`: ข้อมูลส่งออกจาก API
- `frames/`: ภาพโปร่งใสทั้งหมด 60 เฟรมที่ 20 fps
- `combat-contact-sheet.png`: เปรียบเทียบท่าตั้งการ์ด เตรียมเหวี่ยง ปะทะ และตามแรง
- `combat-timeline.json`: เวลาและค่ามุมที่ใช้สร้างแต่ละท่า
- `asset-manifest.json`: พิกัดชิ้นภาพและ hash ของต้นฉบับ
- `agent-session.json`: คำขอ/คำตอบจริง 134 ครั้งในการสร้างและตรวจโปรเจกต์
- `export-session.json`, `preview-metadata.json`: คำสั่งส่งออกและการตรวจว่าภาพทั้ง 60 เฟรมอยู่ภายในกรอบ

## ทำซ้ำ

ใช้ Python ที่มี Pillow และแอปที่ build แล้ว:

```sh
python3 scripts/extract_inquisitor_assets.py
python3 scripts/create_inquisitor_demo.py
python3 scripts/export_inquisitor_demo.py
ffmpeg -framerate 20 -i examples/inquisitor/frames/%03d.png -vf 'scale=768:768:flags=lanczos,format=yuv420p' -c:v libx264 -movflags +faststart examples/inquisitor/Inquisitor-combat.mp4
```

สคริปต์เขียนทับเฉพาะเดโม Inquisitor ไม่แก้เดโม Baldr หรือต้นฉบับ การแยกชิ้นเลือกกลุ่ม alpha ที่เชื่อมต่อใหญ่ที่สุดเพื่อไม่ติด caption; บางชิ้นกลับซ้าย–ขวา และกางเกงแยกซ้าย/ขวาที่กึ่งกลางเพื่อผูกกับขาคนละกระดูก ภาพทั้งหมดรักษาสีและรายละเอียดเดิม
