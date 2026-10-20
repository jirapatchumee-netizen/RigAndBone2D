# ลากเรียง Layer จากรายการฝั่งซ้าย

บันทึกงานที่เปิดอยู่ แล้วเปิด `dist/RigAndBone2D.app` ใหม่เพื่อใช้รายการ Layers รุ่นล่าสุด

1. เลือก **Layers** ด้านซ้าย
2. ลากชื่อชิ้นขึ้นหรือลง และปล่อยระหว่างแถว
3. แถวบนอยู่ด้านหน้า แถวล่างอยู่ด้านหลัง โปรแกรมปรับตัวเลข Layer ให้อัตโนมัติ
4. กด **Save…** เพื่อบันทึกลำดับ

เลือก **Bones** เมื่อต้องการดูโครงสร้างพ่อ–ลูก การเรียงภาพเปลี่ยนเฉพาะค่า layer และไม่เปลี่ยน parent, ลำดับกระดูก, ตำแหน่งภาพ หรือคีย์เฟรม เลือกชิ้นเดียวกันได้จากทั้งสองมุมมอง กระดูกที่ไม่แสดงภาพยังอยู่ในรายการพร้อมป้าย [hidden]

## ผลตรวจ

Build ผ่านและลงลายเซ็น ad hoc แล้ว ทดสอบ native table drag ขึ้นและลงในแอปทดสอบที่ใช้ binary เดียวกับ release เพื่อไม่รบกวนโปรเจกต์ที่ผู้ใช้เปิดอยู่

- `before.jpg`, `drag-up.jpg`, `drag-down.jpg` เป็นภาพหน้าจอจริง
- `Layers-front.rig2d` และ `Layers-back.rig2d` บันทึกผ่าน GUI หลังลากขึ้นและลง
- `gui-proof.json` ตรวจลำดับที่บันทึกและพิกเซลตรงตำแหน่งภาพซ้อน ส่วนข้อมูลที่ไม่ใช่ layer ต้องเหมือนเดิมทั้งหมด
- `gui-readback.json` เป็น API session ที่เปิดไฟล์ GUI และ render ยืนยันผล
- ตรวจสลับ Layers/Bones แล้วเลือกกระดูกเดิมได้ถูกต้อง

ผ่าน `layer_ordering.py` 4 tests รวม native PNG และ sprite sheet, `agent_smoke.py`, `agent_workflow.py` 15 tests, `bone_editing.py` 5 tests, `render_orientation.py`, `demo_reproducibility.py`, `image_offsets.py` 4 tests และ `asset_replacement.py` 5 tests การตรวจทานแยกไม่พบข้อผิดพลาดที่ต้องแก้
