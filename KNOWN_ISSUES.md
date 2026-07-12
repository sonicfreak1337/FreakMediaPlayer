# Known Limitations

- Freak Media Player 1.0 supports local audio only; network and streaming providers
  are intentionally out of scope.
- 5.1 and 7.1 availability depends on the selected Windows device, driver and
  Windows speaker configuration. Unsupported modes are hidden.
- File association is an optional per-user `Open with` registration script rather
  than a system-wide installer change.
- A restored backup or full settings reset requires an application restart.
- The portable build must remain writable if its local `data` directory is used.
- Track-change notifications, tray behavior and the experimental Up Next controls
  are intentionally absent from the UI.

