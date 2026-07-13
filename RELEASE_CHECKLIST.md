# Release Checklist

Final 1.1.0 Windows artifact smoke test: **passed on 2026-07-13**. The executable
hash is recorded in `SHA256SUMS.txt`.

## Automated gate

1. `python -m ruff check src tests`
2. `python -m mypy src`
3. `python -m pytest -q`
4. `build.bat`
5. Start `dist\FreakMediaPlayer\FreakMediaPlayer.exe` on a clean Windows user.

## Manual smoke test

1. Fresh start: skip and complete onboarding once each.
2. Import MP3, FLAC, M4A/ALAC, OGG/Opus, WAV and WMA samples where available.
3. Verify search, metadata fallback, favorite, cover override and folder rescan.
4. Create/reorder/export/import playlists; verify Delete only removes rows.
5. Exercise Play/Pause/Seek/Stop/Next, volume, Shuffle and all Repeat modes.
6. Change audio device and Mono/Stereo mode during playback; verify position resume.
7. On configured hardware, play channel-ID samples in 5.1 and 7.1.
8. Exercise Equalizer, all Visualizer quality levels, skins and dock restore.
9. Export backup, mutate data, restore and restart; confirm recovery and safety copy.
10. Open Diagnostics/log folder and verify About/license information.
11. Test command-line audio opening, portable mode and file-association removal.

## Internet Radio plugin 1.0 gate

Automated coverage uses only local servers and generated media. Before distributing
a Windows build, perform this short public-network smoke test:

1. Enable and disable Internet Radio in Settings and restart after each change.
2. Open the separate radio window and confirm the player dock layout never changes.
3. Play one MP3, AAC/AAC+, Ogg/Opus and HLS station where currently available.
4. Confirm ICY song/artist plus the permanent station name in the main Player.
5. Switch stations repeatedly; test Pause, Stop, mute, output device, EQ and Visualizer.
6. Disconnect/reconnect the network and confirm bounded retries and offline local views.
7. Exercise favorites, individual/complete history deletion, own URL test/edit,
   JSON/M3U8 transfer, logo-cache clearing and `.freakbackup` restore.
8. Leave a stable station playing through standby/wakeup and a multi-hour session;
   confirm no stuck decoder thread or permanently blocked playback state.

## Upgrade and removal

- Upgrade: back up first, replace program files, retain the data directory, start
  once and confirm schema migration. Downgrades across schema changes are unsupported;
  restore the pre-upgrade backup when returning to an older release.
- Installed-folder removal: delete program files. User data is intentionally kept
  below `%LOCALAPPDATA%\FreakMediaPlayer`; delete it separately only when unwanted.
- Portable removal: unregister file associations if used, then delete the portable
  folder. Its local `data` folder contains all portable user data.
