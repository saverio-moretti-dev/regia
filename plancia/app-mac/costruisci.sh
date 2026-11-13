#!/bin/zsh
# Costruisce Regia.app in plancia/app-mac/build/ e (con --installa) la copia in ~/Applications.
set -euo pipefail
cd "${0:A:h}"
B=build/Regia.app
rm -rf build; mkdir -p "$B/Contents/MacOS" "$B/Contents/Resources" build/tmp
swiftc -O -o "$B/Contents/MacOS/Regia" main.swift
cp Info.plist "$B/Contents/Info.plist"
# Icona: icona/AppIcon.icon (Icon Composer) → actool → Assets.car (chiaro, scuro, colorato, trasparente) + AppIcon.icns di riserva.
# actool non si ferma se il nome non è AppIcon.icon: si controlla che abbia scritto i file.
xcrun actool icona/AppIcon.icon --compile build/tmp --platform macosx \
  --minimum-deployment-target 26.0 --app-icon AppIcon \
  --output-partial-info-plist build/tmp/partial.plist \
  --output-format human-readable-text --errors --warnings >build/tmp/log 2>&1 || { cat build/tmp/log; exit 1; }
[[ -f build/tmp/Assets.car && -f build/tmp/AppIcon.icns ]] || { cat build/tmp/log; echo "actool non ha scritto l'icona"; exit 1; }
cp -X build/tmp/Assets.car build/tmp/AppIcon.icns "$B/Contents/Resources/"
rm -rf build/tmp
codesign --force --deep -s - "$B"
echo "costruita: $PWD/$B"
if [[ "${1:-}" == "--installa" ]]; then
  mkdir -p ~/Applications
  pkill -x Regia 2>/dev/null || true
  rm -rf ~/Applications/Regia.app
  cp -R "$B" ~/Applications/Regia.app
  echo "installata: ~/Applications/Regia.app"
fi
