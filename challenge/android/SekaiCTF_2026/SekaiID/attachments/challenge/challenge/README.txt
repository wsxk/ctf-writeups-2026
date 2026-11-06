This folder holds EVERYTHING challenge-specific. It is copied into the image
at /opt/challenge (referenced from setup.sh as $CHALLENGE_DIR).

  setup.sh              <- edit this: your provisioning (runs as root, /system RW)
  <your>.apk            -> $CHALLENGE_DIR/<your>.apk  (auto-installed by setup.sh)
  flag.txt / assets...  -> $CHALLENGE_DIR/...         (push them in setup.sh)

How the pieces fit together:
  ../start.sh           generic emulator/ADB/lockdown orchestration (don't edit)
  ./setup.sh            YOUR challenge provisioning. start.sh runs it while the
                        device is rooted and /system is writable, with adb
                        already targeting the emulator (ANDROID_SERIAL set).

Any *.apk dropped here is auto-installed by the template setup.sh; add custom
steps (seed the flag, set perms, etc.) in setup.sh. With no apk and an
unedited setup.sh, the emulator still boots and locks down root — just with
nothing pre-installed.
