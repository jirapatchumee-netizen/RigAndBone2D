# RigAndBone2D

เครื่องมือสร้างแอนิเมชันตัวละคร 2D แบบแยกชิ้นและกระดูก (2D Skeletal Animation) พร้อม Forward Kinematics, Timeline Keyframing และระบบส่งออก Sprite Sheet

🌐 **Web Edition (ออนไลน์):** [https://jirapatchumee-netizen.github.io/RigAndBone2D/](https://jirapatchumee-netizen.github.io/RigAndBone2D/)  
*(เปิดใช้งานได้ทันทีบนทุกเบราว์เซอร์ ไม่ต้องติดตั้งโปรแกรม รองรับ Windows, Mac, iPad, Android)*

---

## ⚡ การรันและพัฒนาเวอร์ชันเว็บ (Web Development)

```sh
# วิธีที่ 1: ดับเบิลคลิกไฟล์นี้ใน Finder หรือรันผ่านเทอร์มินัล
./RigAndBone2D-Web.command

# วิธีที่ 2: รันผ่านคำสั่ง npm
cd web
npm run dev
```

- มีระบบ **Hot Module Replacement (HMR)** แก้ไขโค้ดใน `web/src/` ปุ๊บ หน้าเว็บจะอัปเดตทันทีแบบเรียลไทม์
- เมื่อพัฒนาเสร็จ แค่รัน `git push origin main` ระบบ **GitHub Actions** จะ Build และ Deploy Patch เวอร์ชันใหม่ขึ้น GitHub Pages ให้อัตโนมัติใน ~30 วินาที

---

## เปิดใช้งานเวอร์ชัน Mac Native App

เปิด `dist/RigAndBone2D.app` หรือรัน:

```sh
open dist/RigAndBone2D.app
```

ต้องการ macOS 14 ขึ้นไป ตัวแอปเป็น arm64 และเซ็นแบบ ad hoc สำหรับใช้ในเครื่องนี้ ยังไม่ได้ notarize เพื่อแจกจ่าย

## การใช้งาน

- เริ่มด้วยตัวละครรูปทรงตัวอย่าง 12 กระดูก (ไม่ได้ใช้ภาพตัวละครของเจ้าของวิดีโอ)
- เลือกกระดูกในรายการ หรือคลิกบนตัวละคร ลากเพื่อหมุน; Shift + ลากเพื่อย้ายตำแหน่งที่ยึดกับกระดูกพ่อ
- Import PNG เปลี่ยนภาพของชิ้นที่เลือก รองรับพื้นหลังโปร่งใส ภาพฝังในไฟล์โปรเจกต์
- ปรับ Parent, Angle, Length, Width และ Pivot X/Y ในแผงด้านขวา
- เลื่อนเวลา จัดท่า แล้วกด Add keyframe; Play / Pause เล่นแบบวนซ้ำ
- Save / Open ใช้ไฟล์ JSON นามสกุล `.rig2d`
- Export sheet ส่งออก PNG โปร่งใส 24 เฟรม (6 × 4 ช่อง ขนาดช่อง 384 × 384) พร้อม JSON ข้อมูลเฟรม

## สำหรับ AI agent

เริ่มที่ [docs/AGENT_API.md](docs/AGENT_API.md) และ [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

```sh
python3 scripts/agent.py '{"id":"discover","command":"capabilities"}'
python3 scripts/agent.py '{"command":"inspect","project":"examples/warrior.rig2d"}'
```

API ทำงานในเครื่อง ไม่ต้องเปิดหน้าต่างแอป ไม่ต้องใช้ OCR หรือจำตำแหน่งปุ่ม ไม่มีการเรียกโมเดลภายนอก

## สร้างและทดสอบ

```sh
./scripts/build-app.sh
python3 tests/agent_smoke.py
```

ใช้ Swift + AppKit ที่ติดมากับ Xcode Command Line Tools ไม่มีไลบรารีภายนอก

## ขอบเขตรุ่น 0.1

มีโครงกระดูกพ่อ–ลูก ภาพแยกชิ้น จุดหมุน ลำดับภาพ คีย์เฟรมมุม และการเปลี่ยนภาพโดยคงโครงกระดูกเดิม
ยังไม่มี mesh skinning, IK, ตัดชิ้นภาพด้วย AI, คลิปแอนิเมชันหลายชุด, autosave หรือชุดเสื้อผ้าสำเร็จรูปแบบในคลิป
คีย์เฟรมเก็บเฉพาะมุม ตำแหน่งและขนาดเป็นค่าของ rig; export มีขนาดคงที่และอาจตัด rig ที่ใหญ่เกินช่อง
หาก agent แก้ไฟล์ที่เปิดอยู่ในแอป ให้ Open ไฟล์นั้นใหม่ก่อนแก้ต่อใน UI

วิดีโออ้างอิง: `references/rigandbone2d_reference.mp4` (247.616 วินาที, 1920 × 1080)

## เดโมจาก asset จริง: Baldr

เปิด `examples/baldr/Baldr.rig2d` ในแอป หรือดู [คู่มือเดโม](examples/baldr/README.md) มีตัวละคร 22 กระดูก แอนิเมชัน 3 วินาที และ sprite sheet ที่สร้างผ่าน Agent API จริง

เปิดและเล่นผ่านคำสั่งได้:

```sh
open -n dist/RigAndBone2D.app --args --project "$(pwd)/examples/baldr/Baldr.rig2d" --play
```

เพิ่ม regression test ภาพ PNG กลับหัว: `python3 tests/render_orientation.py` (ต้องมี Pillow)

## เดโมที่ 2: Inquisitor ต่อสู้ด้วย Morning Star

เปิด `examples/inquisitor/Inquisitor-combat.rig2d` มีจังหวะเตรียมเหวี่ยง ฟาดหุ่นฝึก โซ่สะบัด และกลับมาตั้งการ์ด 13 คีย์เฟรม วน 3 วินาที พร้อม preview 60 เฟรมที่ 20 fps ดู [คู่มือเดโมต่อสู้](examples/inquisitor/README.md)

## ระบบสำหรับงานถัดไป — รุ่น 0.2

เริ่มที่ [คู่มือ workflow สำหรับ agent](docs/AGENT_WORKFLOW.md) ใช้ [recipe ของ Baldr](recipes/baldr.rigrecipe.json) และ [recipe ต่อสู้](recipes/inquisitor-combat.rigrecipe.json) เป็นตัวอย่าง

ตัวละครใหม่ประกาศข้อมูลใน JSON: ID กระดูก, parent, ภาพ, pivot และ pose ไม่ต้องเขียนสคริปต์ประกอบเฉพาะตัวอีก ใช้ `scripts/rig_pipeline.py` ตัวเดียวสำหรับ prepare / build / check / preview

API เพิ่ม stable IDs, recipe compilation, batch ที่บันทึกครั้งเดียว, dry run, revision receipts และรหัสข้อผิดพลาด มี writer lock และตรวจ revision สำหรับป้องกันการเขียนจากข้อมูลเก่า ทั้ง GUI และ API ใช้ ProjectStore เดียวกัน ไฟล์เดโมเดิมยังใช้ได้

```sh
python3 scripts/rig_pipeline.py build recipes/inquisitor-combat.rigrecipe.json --project scratch/next-job/Character.rig2d --dry-run
python3 scripts/rig_pipeline.py build recipes/inquisitor-combat.rigrecipe.json --project scratch/next-job/Character.rig2d
python3 scripts/rig_pipeline.py check scratch/next-job/Character.rig2d --strict
```

## Godot bridge

Native cutout Scene export with a shared, trimmed, downsampled and deduplicated atlas. See [Godot handoff contract](docs/GODOT_HANDOFF.md). Open `examples/godot-demo/project.godot` in Godot: Left/Right move; Space attacks the training target. `tests/godot_bridge.py` checks resource sharing, pose equivalence, native import and damage behavior (Pillow + Godot required).

## SpriteKit bridge

Baked clip export for native iPhone games: `scripts/rig_pipeline.py spritekit-export PROJECT --config CONFIG --output NEW_DIRECTORY` (Pillow required). The native renderer/sampler remain authoritative. The immutable package contains a trimmed, deduplicated atlas and a versioned manifest with pinned source revision, original-canvas pivots, clip timings and visual events. See [SpriteKit handoff contract](docs/SPRITEKIT_HANDOFF.md). Run `tests/spritekit_bridge.py` for exact rendered-pixel parity, orientation, extrusion, relocation, budget and revision rejection checks. This bridge does not export mesh deformation or a runtime skeleton.

## Chibi cutout และการเปลี่ยนภาพเฉพาะชิ้น

เปิด `examples/chibi-20261020/Chibi.rig2d` เพื่อดู rig 17 กระดูกจากภาพที่แยกเป็น PNG 16 ชิ้น พร้อม idle ตัวอย่าง 2 วินาที อ่านผลวิเคราะห์และข้อจำกัดของขอบภาพกับรอยต่อใน [รายงาน Chibi](reports/chibi-20261020/analysis.md)

เลือกกระดูกแล้วกด **Replace PNG…** ใน inspector เพื่อเปลี่ยนเฉพาะภาพ โดยคงขนาด จุดหมุน parent และคีย์เฟรมเดิม API ใช้ `replace_image` และรองรับ `batch`, `dry_run`, `expected_revision` ผ่าน ProjectStore เดิม ภาพใหม่ต้องจัด canvas และตำแหน่งข้อต่อให้ตรงกัน ส่วน **Import PNG…** ยังคำนวณความกว้างตามสัดส่วนภาพ

ทดสอบด้วย Python ที่มี Pillow โดยรัน `python3 tests/asset_replacement.py` ตัวอย่างนี้ยังต้องเก็บขอบและรอยต่อก่อนส่งเกม และยังไม่มีคลัง skin หลายชุดในโปรเจกต์

## จัดภาพและเพิ่มหรือลบกระดูกด้วยตัวเอง

- เลือกชิ้นในรายการ แล้วเปิด **Move image** เพื่อใช้เมาส์ลากเฉพาะภาพ ข้อต่อและกระดูกลูกอยู่ที่เดิม
- ปรับ **Image X / Image Y** เพื่อเลื่อนภาพอย่างละเอียด ค่านี้อิงแกนของกระดูกและใช้กับทุกคีย์เฟรม
- **Reset image position** คืนตำแหน่งภาพให้ตรง pivot เดิม ลากชื่อในรายการซ้ายเพื่อกำหนดชิ้นที่ซ้อนอยู่ด้านหน้า
- **Add child bone** เพิ่มกระดูกลูกของชิ้นที่เลือก ปุ่ม **Add bone** ด้านบนใช้คำสั่งเดียวกัน
- **Delete bone…** แสดงจำนวนกระดูกลูกก่อนยืนยันลบทั้งกิ่ง คีย์เฟรมของกระดูกที่เหลือถูกปรับตามรายการใหม่ ใช้ ⌘Z เพื่อย้อนการลบได้
- ปิด Move image เพื่อกลับไปลากหมุนกระดูก หรือ Shift-drag เพื่อย้ายข้อต่อ แล้วกด **Save…** เพื่อเก็บงาน

ไฟล์เดิมที่ไม่มีค่าเลื่อนภาพเปิดได้ตามเดิม การเปลี่ยน PNG เก็บตำแหน่งภาพที่จัดไว้ และการส่งออก PNG, Godot, SpriteKit ใช้ตำแหน่งเดียวกับหน้าจอ

## ลากชื่อเพื่อจัดลำดับภาพและ Undo

แผงซ้ายมีรายชื่อเดียว ลากชื่อขึ้นเพื่อให้อยู่ด้านหน้า หรือลงเพื่อให้อยู่ด้านหลัง ไม่มีโหมดให้สลับและไม่มีช่องกรอก Layer ตัวเลข การลากเปลี่ยนเฉพาะลำดับภาพ โครงกระดูกพ่อ–ลูกและแอนิเมชันยังเหมือนเดิม

ใช้ **⌘Z** เพื่อ Undo และ **⌘⇧Z** เพื่อ Redo หรือใช้เมนู **Edit** รองรับการเรียงภาพ ลากภาพหรือกระดูก แก้คุณสมบัติ เพิ่มและลบกระดูก เปลี่ยนภาพ และคีย์เฟรม หนึ่งครั้งที่ลากเป็นหนึ่งรายการย้อนกลับ ประวัติเก็บได้ 100 รายการในครั้งที่เปิดโปรเจกต์ บันทึกไฟล์แล้ว Undo ต่อได้ การเปิดหรือสร้างโปรเจกต์ใหม่จะเริ่มประวัติใหม่

ระหว่างพิมพ์ในช่องข้อความ ⌘Z ย้อนข้อความที่พิมพ์ กด Enter และคลิกรายการซ้ายหรือพื้นที่ทำงานเพื่อย้อนการแก้โปรเจกต์

## ซูมและปรับ rig บน workspace

- หมุนลูกกลิ้งเมาส์เหนือ workspace เพื่อซูมเข้าออก โดยยึดตำแหน่งใต้เคอร์เซอร์ กดลูกกลิ้งค้างแล้วลากเพื่อเลื่อนมุมมอง
- กด **Fit** เพื่อจัดตัวละครในท่าปัจจุบันให้พอดีพื้นที่ ภาพและกระดูกจะถูกตัดตามขอบ workspace เมื่อซูมเข้า
- เลือกกระดูกแล้วลากลูกศร **X สีแดง** หรือ **Y สีเขียว** เพื่อย้ายข้อต่อตามแกน ลากสี่เหลี่ยมตรงกลางเพื่อย้ายอิสระ กระดูกลูกจะตามไปด้วย เปิด **Bones** และปิด **Move image** เพื่อเห็นเครื่องมือ
- แผง **Bone Properties** มี slider สำหรับตำแหน่ง ขนาด มุม จุดหมุนและตำแหน่งภาพ เลื่อนแผงลงเพื่อดูรายการด้านล่าง ยังพิมพ์ค่าที่ช่องตัวเลขได้ หนึ่งครั้งที่ลาก slider หรือแกนย้อนกลับด้วย **⌘Z** ได้

มุมมองซูมและเลื่อนเป็นค่าของหน้าต่าง ไม่เปลี่ยนข้อมูล rig หรือขนาด export คีย์เฟรมยังเก็บเฉพาะมุม ส่วนตำแหน่งข้อต่อเป็นการปรับโครง rig ตลอดแอนิเมชัน
