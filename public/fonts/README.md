# Fonts Directory

This directory contains custom fonts for the Blockchain Explorer application.

## Required Font Files

The application expects the following font files:

1. **BlockchainFont-Regular.woff2** and **BlockchainFont-Regular.woff**
   - Regular weight font for the main UI

2. **BlockchainFont-Bold.woff2** and **BlockchainFont-Bold.woff**
   - Bold weight font for headings

3. **TechMono-Regular.woff2** and **TechMono-Regular.woff**
   - Monospace font for code and hash displays

## Note

If you don't have custom fonts, the application will fall back to system fonts:
- BlockchainFont → system sans-serif fonts
- TechMono → system monospace fonts (Courier New, etc.)

The fonts are referenced in `public/index.html` and will be loaded automatically when available.
