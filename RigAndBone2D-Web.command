#!/bin/bash
# RigAndBone2D Web Dev Server Launcher
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR/web" || exit 1

echo "⚡ Starting RigAndBone2D Web Development Server..."
npm run dev -- --open
