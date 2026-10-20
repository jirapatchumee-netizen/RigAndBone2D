# Baldr — demo 1 ตัวละคร

สร้างจาก sprite sheet ที่ผู้ใช้ให้ โดยแยกชิ้นภาพจริงและคง alpha เดิม ตัวละครมี 22 กระดูก, 7 คีย์เฟรม และแอนิเมชันวน 3 วินาที: idle, ขยับปีก/ผ้าคลุม และยกแขน ไม่มี mesh deformation

## เปิดในแอป

จากโฟลเดอร์โปรเจกต์:

```sh
open -n dist/RigAndBone2D.app --args --project "$(pwd)/examples/baldr/Baldr.rig2d" --play
```

หรือกด Open ในแอป แล้วเลือก `Baldr.rig2d` ภาพทุกชิ้นฝังในโปรเจกต์แล้ว ไม่ต้องเลือก asset ใหม่

## ผลลัพธ์

- `Baldr.rig2d`: โปรเจกต์ที่แก้และเล่นต่อได้
- `Baldr-preview.png`, `Baldr-salute.png`: ภาพท่าเริ่มและท่ายกแขน
- `Baldr-sheet.png`: 24 เฟรมโปร่งใส 2304 × 1536, 6 คอลัมน์ × 4 แถว, ช่อง 384 × 384
- `Baldr-sheet.json`: ข้อมูลส่งออกจาก API; 8 เฟรมต่อวินาทีเมื่อเล่นครบ 3 วินาที
- `Baldr-demo.gif`, `Baldr-demo.mp4`: ตัวอย่างเคลื่อนไหวจากเฟรมที่แอปส่งออกจริง
- `Baldr-app.png`: screenshot ของหน้าต่างแอปที่โหลดเดโม
- `asset-manifest.json`: พิกัดตัดชิ้นและ SHA-256 ของไฟล์ต้นฉบับ
- `agent-session.json`: คำขอ/คำตอบจริง 120 ครั้งในการสร้างและตรวจเดโม
- `export-session.json`: คำสั่งส่งออกจริงและผลลัพธ์

## ทำซ้ำ

ต้องใช้ Python ที่มี Pillow, Swift Command Line Tools; ffmpeg ใช้เฉพาะเมื่อต้องการ MP4

```sh
./scripts/build-app.sh
python3 scripts/extract_baldr_assets.py
python3 scripts/create_baldr_demo.py
python3 scripts/export_baldr_demo.py
```

สคริปต์สร้างเดโมจะเขียนทับเฉพาะโปรเจกต์เดโมนี้ ใช้ API ของแอปสำหรับการสร้างกระดูก นำเข้าภาพ จัดท่า คีย์เฟรม ตรวจความถูกต้อง และเรนเดอร์ ไม่เขียน JSON โปรเจกต์ด้วยตนเอง; ส่ง expected_revision จาก inspect ก่อนแก้แต่ละชิ้น

ชิ้นส่วนซ้าย–ขวาบางชิ้นใช้ภาพเดียวกันหรือกลับซ้าย–ขวาจากต้นฉบับ การจัดสัดส่วนและท่าทางเป็นเดโมที่ประกอบขึ้นใหม่ ไม่ใช่แอนิเมชันต้นฉบับของเกม
