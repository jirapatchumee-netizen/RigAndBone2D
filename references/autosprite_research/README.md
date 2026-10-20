# รายงานการวิจัยและวิเคราะห์การทำงาน: autosprite.app (Sloth Studio)

เอกสารฉบับนี้สรุปผลการ Reverse Engineering และวิเคราะห์เจาะลึกกระบวนการทำงานของแอปพลิเคชัน **`autosprite.app`** (ชื่อโปรดักชันคือ **Sloth Studio** หรือชื่อภาษาไทยในระบบ **"สลอธ สตูดิโอ"**, Bundle ID: `com.wails.stupidagent`, เวอร์ชัน `0.2.1`) ซึ่งเป็นเครื่องมือสร้างสไปรต์การเดิน 8 ทิศทาง (8-directional walking sprite sheet) จากภาพนิ่งตัวละคร 1 ภาพด้วย Generative AI

---

## 1. ข้อมูลทั่วไปและสถาปัตยกรรมระบบ (System Architecture)

ตัวโปรแกรมสร้างขึ้นด้วยเฟรมเวิร์ก **Wails v2** (Go + Web Frontend) ซึ่งรันเป็นแอปเนทีฟบน macOS โดยไม่ต้องพึ่ง Electron:

* **Executable Binary:** `Contents/MacOS/sloth-studio` (Mach-O Universal Binary รองรับ `arm64` และ `x86_64`, ขนาด ~43MB)
* **Backend:** ภาษา Go 1.2x รับหน้าที่จัดการ State, Task Queue, File I/O, SQLite DB, และเชื่อมต่อ API ภายนอก
* **Frontend:** React + Tailwind CSS SPA ถูกบันทึกและรันผ่าน Go `embed.FS` จาก `frontend/dist/assets/index-BuYjq1-v.js` (มีระบบภาษา อังกฤษ / ไทย)
* **Embedded Database:** SQLite จัดการผ่าน `bun` ORM / migration
* **External AI Integration:** เชื่อมต่อไปยัง **OpenRouter API** (`https://openrouter.ai/api/v1`) โดยใช้ API Key ที่ผู้ใช้ระบุใน Settings
* **License & Sync Server:** เชื่อมต่อไปยัง `https://slothstudio.supercapybara.com` สำหรับการตรวจสอบสิทธิ์การส่งออกไฟล์

```
+---------------------------------------------------------------------------------+
|                                 SLOTH STUDIO                                    |
|                                                                                 |
|   +-------------------------------------------------------------------------+   |
|   |                       Frontend UI (WebKit / React)                      |   |
|   | - Character Reference Upload & Prompt Input                             |   |
|   | - Interactive 8-directional Stills Reviewer & Approver                  |   |
|   | - HTML5 Video Frame Sampler (Canvas 24fps Seeker & toDataURL)           |   |
|   | - Sprite Loop Selector (First/Last Frame Picker & Gap Filling)          |   |
|   +-----------------------------------+-------------------------------------+   |
|                                       | IPC via window.go.main.*                |
|                                       v                                         |
|   +-------------------------------------------------------------------------+   |
|   |                       Backend Engine (Go / Wails)                       |   |
|   |                                                                         |   |
|   |  [QueueService]                                                         |   |
|   |  - EnqueueWalkLab / EnqueueSpriteSheet / Retry / Worker loop            |   |
|   |                                                                         |   |
|   |  [WalkLab Processor]                                                    |   |
|   |  - 4x2 Grid Slicer (splitWalkLabComposite / splitEightStills)           |   |
|   |  - Alpha Bounding & Centering (alphaBounds / nontransparentBounds)      |   |
|   |  - Chroma Key Removal (chromaness / chromaRGB / keyWalkFrame)           |   |
|   |  - Loop Analyzer (SuggestSpriteLoop / loopDifference / loopCandidate)  |   |
|   |                                                                         |   |
|   |  [Local Store (SQLite)]                                                 |   |
|   |  - jobs, spritegen_assets, settings, local_license_state                |   |
|   +-----------------------------------+-------------------------------------+   |
+---------------------------------------|-----------------------------------------+
                                        |
                 +----------------------+----------------------+
                 | HTTP Requests                               |
                 v                                             v
    +---------------------------+                +---------------------------+
    |      OpenRouter API       |                |      License Server       |
    | - Image Generation Model  |                | slothstudio.supercapybara |
    | - Video Gen (Hailuo 3 Max)|                | - License & Run Receipts  |
    +---------------------------+                +---------------------------+
```

---

## 2. ขั้นตอนการทำงานแบบเจาะลึก (WalkLab Pipeline)

หัวใจของแอปคือฟีเจอร์ที่ชื่อว่า **WalkLab** ซึ่งแบ่งการทำงานออกเป็น 6 สเต็ปอย่างเป็นระบบ:

### สเต็ปที่ 1: การป้อนภาพอ้างอิงและพรอมป์ (Character Reference)
* ผู้ใช้อัปโหลดภาพตัวละครด้านหน้า (`front`) และสามารถใส่คำอธิบายเพิ่มเติม เช่น สีเสื้อผ้า สไตล์ ซิลูเอต (`characterPrompt`)
* ภาพจะถูกแปลงเป็น Data URL (`data:image/png;base64,...`) เก็บชั่วคราวในฝั่งฟรอนต์เอนด์

### สเต็ปที่ 2: การสร้างภาพนิ่ง 8 ทิศทางด้วยเทคนิค 4×2 Grid (8-Directional Stills)
ปัญหาใหญ่ของการเจนภาพ 8 มุมทีละครั้งคือ **"หน้าตาและชุดจะเปลี่ยนไปเรื่อยๆ (Character Inconsistency)"** 
autosprite แก้ปัญหานี้อย่างชาญฉลาดโดย **ส่งคำขอสร้างภาพเพียงครั้งเดียว** ให้ได้ภาพตาราง 4 คอลัมน์ × 2 แถว:

* **Prompt Template ที่ดึงมาจาก Binary:**
  > *"Create exactly one composite image containing eight full-body views of the same character from the front-facing image. Use a borderless four-column, two-row grid with equal cells and no gaps. In reading order, the top row is front, front-right, right, back-right; the bottom row is back, back-left, left, front-left. Place exactly one centered character in each cell, with transparent space around it. Keep clothing, colors, proportions, and camera distance consistent. Return one image only; the app will crop and center the eight cells. Do not include labels, grid lines, or extra characters."*

* **การตัดและจัดกึ่งกลางภาพ (`splitWalkLabComposite` / `splitEightStills`):**
  1. โปรแกรมตรวจสอบว่าภาพเป็นตาราง 4×2 บนพื้นหลังโปร่งใส (Transparent PNG)
  2. ตัดแบ่งออกเป็น 8 ช่องตามลำดับการอ่าน:
     * **แถวที่ 1:** `front`, `front-right`, `right`, `back-right`
     * **แถวที่ 2:** `back`, `back-left`, `left`, `front-left`
  3. ฟังก์ชัน `alphaBounds` ตรวจสอบหา Bounding Box ของพิกเซลที่ไม่โปร่งใสในแต่ละช่อง
  4. ทำการจัดให้ตัวละครอยู่ตรงกลางกรอบเท่ากันทุกมุม
  5. หากบางมุมผิดพลาด ผู้ใช้สามารถกด "Regenerate still" เฉพาะมุมนั้นได้ โดยระบบจะส่งพรอมป์:
     > *"full-body still from the character image. Match the other directions' clothing, colors, proportions, camera distance, and transparent background. Do not change other directions."*

### สเต็ปที่ 3: การสร้างวิดีโอแอนิเมชันการเดิน (Walking Loop Video)
เมื่อผู้ใช้ตรวจและยืนยันภาพนิ่งทั้ง 8 ทิศทางแล้ว โปรแกรมจะส่งคำขอไปยังโมเดลวิดีโอ:
* **โมเดลที่เรียกใช้:** `minimax/hailuo-3-max` ผ่าน OpenRouter Video API (`/videos`)
* **Chroma-Key Background:** ผู้ใช้เลือกสีพื้นหลังที่ไม่ซ้ำกับสีของตัวละคร:
  * เขียว: `#00FF00`
  * ชมพูม่วง (Magenta): `#FF00FF`
* **Prompt Template สำหรับวิดีโอเดิน:**
  > *"seamless walking loop from its approved still. The first frame already shows the entire character with generous empty space around the hood, hands, and feet; preserve that exact small full-body scale and center in every frame. Keep the hood and both feet fully inside the frame throughout the walk. Walk in place with no camera movement, zoom, reframing, extra objects, or background changes. Use a completely flat, uniform chroma-key background of exactly [CHROMA_COLOR]..."*

### สเต็ปที่ 4: การสกัดเฟรมวิดีโอในฝั่งไคลเอนต์ (Client-side Frame Extraction)
แทนที่จะติดตั้ง FFmpeg ซึ่งทำให้ขนาดแอปใหญ่ขึ้น Wails ใช้ความสามารถของเบราว์เซอร์ WebKit บน macOS:
* สร้างแท็ก `<video>` โหลดไฟล์ MP4 ที่ได้จาก OpenRouter
* สร้างแท็ก `<canvas>` ขนาดคำนวณตามสัดส่วน (สูงสุด 1024px)
* ทำการ Seek วิดีโอไปทีละตำแหน่งเวลา `currentTime = D` (คำนวณจาก `duration` ที่ 24 fps สูงสุด 144 เฟรม)
* แคปเจอร์ลง Canvas แล้วแปลงเป็น Data URL (`toDataURL("image/png")`)
* ส่งเฟรมทั้งหมดกลับมาให้ Go Backend บันทึกผ่าน `SaveSpriteLoopFrames`

### สเต็ปที่ 5: การลบพื้นหลัง Chroma Key & การหา Loop เดินอัตโนมัติ (`SuggestSpriteLoop`)
* **การลบพื้นหลัง:** Go backend ประมวลผล `keyWalkFrame` และ `chromaness` โดยคำนวณระยะห่างของสีเทียบกับ Chroma Color ที่เลือกไว้ พิกเซลที่ตรงกับสีพื้นหลังจะถูกปรับค่า Alpha ให้เป็น 0
* **อัลกอริทึมหาจุดวนลูปที่ดีที่สุด (`walklab_loop_suggest.go`):**
  * โค้ดมีฟังก์ชัน `loopDifference`, `loopPixel`, `loopCandidate`, `pickLoop`, `chooseLoop`
  * ระบบจะสแกนเฟรมทั้งหมด คำนวณความต่างเชิงพิกเซล (Pixel difference / MSE) ระหว่างเฟรม เพื่อหาคู่เฟรม `first` และ `last` ที่มีท่าทางการก้าวขาและการวางแขนใกล้เคียงกันที่สุด
  * ทำให้ได้ช่วงเฟรมที่นำมาเล่นวนลูป (Loop) แล้วตัวละครไม่สะดุดหรือกระตุก
  * ฟังก์ชัน `Fill missing frames` ช่วยเลือกเฟรมที่จำเป็นเพื่อให้ความเร็วการเดินสอดคล้องกับ Frame Rate ที่ผู้ใช้เลือก

### สเต็ปที่ 6: การประกอบสไปรต์ชีตและส่งออก (Sprite Sheet Export)
* ฟังก์ชัน `QueueService.EnqueueSpriteSheet` จะนำเฟรมของทั้ง 8 ทิศทางมารวมเป็น:
  1. **Sprite Sheet Image (`.png`):** ภาพ Atlas รวมทุกเฟรมของ 8 ทิศทาง
  2. **Metadata File (`.json`):** ข้อมูลทิศทาง, จำนวนเฟรม, พิกัด `x, y, w, h`, จุด Pivot, และ Frame Rate
* บันทึกไฟล์ไปยังโฟลเดอร์ `~/Downloads` ของเครื่องผู้ใช้

---

## 3. ฐานข้อมูลภายใน (SQLite Schema)

แอปใช้ SQLite เก็บสถานะงานและ Asset ต่างๆ เพื่อให้ปิดเปิดแอปแล้วงานไม่หาย:

```sql
-- คิวงานประมวลผล (Jobs Queue)
CREATE TABLE jobs (
  id TEXT PRIMARY KEY,
  type TEXT NOT NULL CHECK (type IN ('spritegen', 'sprite-sheet', 'text-file')),
  payload TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('pending', 'running', 'blocked', 'done', 'failed', 'cancelled')),
  progress INTEGER NOT NULL DEFAULT 0,
  attempts INTEGER NOT NULL DEFAULT 0,
  run_after TEXT NOT NULL,
  result TEXT NOT NULL DEFAULT '',
  error TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

-- การจัดการ Asset แต่ละทิศทาง
CREATE TABLE spritegen_assets (
  kind TEXT NOT NULL,                -- 'still', 'walkVideo', 'walkChroma', 'loopFrames'
  direction TEXT NOT NULL DEFAULT '', -- 'front', 'front-right', 'right', 'back-right', 'back', 'back-left', 'left', 'front-left'
  path TEXT NOT NULL,
  job_id TEXT,
  updated_at TEXT NOT NULL,
  PRIMARY KEY (kind, direction),
  FOREIGN KEY (job_id) REFERENCES jobs(id)
);

-- การตั้งค่าผู้ใช้
CREATE TABLE settings (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);

-- สถานะสิทธิ์การใช้งาน (License State)
CREATE TABLE local_license_state (
  id INTEGER PRIMARY KEY CHECK (id = 1),
  machine_id TEXT NOT NULL,
  state TEXT NOT NULL,
  usage_count INTEGER NOT NULL CHECK (usage_count >= 0),
  issued_at INTEGER NOT NULL,
  expires_at INTEGER NOT NULL,
  signed_receipt TEXT NOT NULL,
  checked_at TEXT NOT NULL
);
```

---

## 4. ข้อสังเกตและแนวทางนำไปประยุกต์ใช้กับ RigAndBone2D

| สิ่งที่ autosprite ทำได้ดี | ข้อจำกัดใน autosprite | แนวทางต่อยอดใน RigAndBone2D |
|---|---|---|
| **4x2 Composite Prompt:** ใช้ 1 รูปเจน 8 ทิศทาง คุมความเหมือนของตัวละครได้ยอดเยี่ยม | มีโอกาสที่บางมุมยังเพี้ยน หรือเท้าไม่ติดพื้นเท่ากัน | นำเทคนิคตาราง 4x2 มาใช้สร้าง Base Reference หรือ Textures สำหรับทิศทางต่างๆ |
| **Chroma Key Walk-in-Place Video:** เจนท่าเดินจากวิดีโอ AI ได้เฟรมที่เป็นธรรมชาติ | เป็นเพียง Flat Sprite (ภาพนิ่งทีละเฟรม) ปรับแต่งท่าทางหรือกระดูกไม่ได้ภายหลัง | ใน RigAndBone2D เราสามารถใช้ภาพนิ่งหรือวิดีโอเหล่านี้เป็น **Motion Reference** สำหรับการแกะ Bone Keyframes / Auto-Rigging |
| **No-FFmpeg WebKit Frame Extractor:** สกัดเฟรมจากวิดีโอผ่าน Canvas ใน WebKit ทำให้ Binary มีขนาดเล็กมาก | ประสิทธิภาพขึ้นกับ Hardware Acceleration ของ WebKit ในเครื่อง | เหมาะมากสำหรับการเขียน GUI ในเครื่อง Mac ที่ไม่ต้องติดตั้ง Dependency หนักๆ เพิ่มเติม |
| **Automated Loop Candidate Scoring:** อัลกอริทึมหาจุดต่อของลูปเดินอัตโนมัติ | คำนวณจากพิกเซลภาพตรงๆ หากมีเงาหรือแสงเปลี่ยนอาจทำให้คะแนนเพี้ยน | ใน RigAndBone2D สามารถใช้ตำแหน่งกระดูก (Bone Rotations / Positions) ในการตรวจจับ Loop Cycle ซึ่งจะแม่นยำกว่าการเทียบพิกเซล |
