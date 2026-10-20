#!/bin/zsh
# ==============================================================================
# RigAndBone2D Launcher for macOS (Apple Silicon)
# - ดับเบิลคลิกไฟล์นี้เพื่อเปิดแอป RigAndBone2D ได้ทันที
# - รองรับการลากไฟล์ .rig2d มาวางใส่ไฟล์นี้เพื่อเปิดโปรเจกต์
# ==============================================================================

set -euo pipefail

# ย้ายไปยัง Directory ที่ไฟล์ .command นี้ตั้งอยู่
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

APP_PATH="$DIR/dist/RigAndBone2D.app"

# ตรวจสอบว่ามีตัวแอปที่ build ไว้แล้วหรือไม่ หากยังไม่มีจะทำการ build ให้อัตโนมัติ
if [ ! -d "$APP_PATH" ] || [ ! -x "$APP_PATH/Contents/MacOS/RigAndBone2D" ]; then
    echo "⚙️  ไม่พบตัวแอปที่ build หรือไฟล์ binary ไม่สมบูรณ์ กำลัง build ใหม่..."
    ./scripts/build-app.sh
fi

# ตรวจสอบว่ามีการลากไฟล์โปรเจกต์ (.rig2d) หรือส่ง argument มาหรือไม่
if [ $# -gt 0 ]; then
    PROJECT_PATH="$1"
    echo "🎨 กำลังเปิด RigAndBone2D พร้อมโปรเจกต์: $PROJECT_PATH"
    open -n "$APP_PATH" --args --project "$PROJECT_PATH"
else
    echo "🚀 กำลังเปิด RigAndBone2D..."
    open "$APP_PATH"
fi

# หน่วงเวลาสั้นๆ ก่อนปิด Terminal เพื่อให้กระบวนการ launch สำเร็จ
sleep 0.5

# พยายามปิดหน้าต่าง Terminal ที่เปิดขึ้นมาโดยอัตโนมัติ (หากรันผ่าน Apple Terminal)
if [[ "${TERM_PROGRAM:-}" == "Apple_Terminal" ]]; then
    osascript -e 'tell application "Terminal" to close (every window whose name contains "RigAndBone2D.command")' >/dev/null 2>&1 &
fi

exit 0
