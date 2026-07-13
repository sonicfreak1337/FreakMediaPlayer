# Known Limitations

- The optional Internet Radio plugin depends on public station-directory and stream
  operators. Individual stations can disappear, change codec or omit song metadata.
- Radio Browser does not consistently provide normalized city data; country, region,
  station-name and free-text discovery remain available when city metadata is absent.
- System proxy discovery is used for directory, playlist and logo HTTP requests.
  FFmpeg stream proxy behavior can additionally depend on its platform build and the
  proxy protocol in use.
- AAC+ uses FFmpeg's shared AAC decoder. A final release smoke test with at least one
  real HE-AAC station remains recommended because the bundled encoder cannot create a
  self-contained HE-AAC fixture for automated tests.
- 5.1 and 7.1 availability depends on the selected audio device, driver and
  operating-system speaker configuration. Unsupported modes are hidden.
- Windows file association remains an optional per-user `Open with` registration
  script. Linux packages register supported audio MIME types through their desktop file.
- A restored backup or full settings reset requires an application restart.
- The portable build must remain writable if its local `data` directory is used.
- Track-change notifications, tray behavior and the experimental Up Next controls
  are intentionally absent from the UI.
