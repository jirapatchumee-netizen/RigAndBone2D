2026-10-01 — ปรับฐานงานตาม owner: T-pose + character sheet ก่อนแยกชิ้นส่วน/ริก
สร้าง CHR-F3-farmer-tpose/master.png และ CHR-F4-farmer-character-sheet/master.png ด้วย imagegen; 1536×1024 RGBA ทั้งคู่
แนบ hero และ happy head ของ F1; เก็บ master ต้นฉบับพร้อม prompt และ DONE; ไม่เปลี่ยนไฟล์ที่อนุมัติแล้ว
T-pose: มุมหน้าตรง แขนเหยียดแนวนอน ขาแยก ปลอกผ้าชั้นเดียว; sheet: หน้า/สามส่วน/ข้าง/หลัง + 4 สีหน้า
ยังมี halo/ระยะขอบไม่ครบตาม prompt; มุมหลังเป็นรายละเอียดที่อนุมาน ต้องให้ owner ดูก่อน; ยังไม่ใช้เป็น production asset
หยุดรอ owner ดูภาพตั้งต้น; v005 เป็นงานทดลอง ไม่ใช่ริกที่ผ่านการอนุมัติ

2026-10-01 — RIG-FARMER-FIX-001: v005 เป็นงานทดลอง ยังไม่ส่งให้ตัดสินผ่าน
เลือก 9 bones; ตัดจาก hero F1 โดยตรงเพื่อคงสี/สัดส่วนและลดปลอกผ้าซ้อน; เพิ่ม prepare_farmer_fix.py และปรับ joint table
rig_run.sh จบ OK v005; strict check/preview ผ่าน; clippedFrames=[]; emptyFrames=[]; atlas 512×1737; เฟรม 288×288
idle 1.0s/15 เฟรม; walk 0.8s/12 เฟรม; แกว่งแขน ±30° ขา ±25°; loop endpoint pose เท่ากัน
ตรวจ native พบเศษที่ไหล่และช่องว่างบางมุม; faint-alpha ratio 3.30–4.08% ยังเกินเกณฑ์ 1%; ไม่อ้างว่าริกผ่าน
owner ปรับทิศทางให้เริ่มจาก T-pose และ character sheet; ทำ CHR-F3/CHR-F4 เพื่อรีวิวฐานภาพก่อนริกรอบถัดไป

