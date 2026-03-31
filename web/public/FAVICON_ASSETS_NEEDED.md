# Favicon Assets Needed

The following image assets need to be created and placed in this directory:

## Required Files

### 1. favicon.ico
- **Size**: 32x32px (can contain multiple sizes: 16x16, 32x32, 48x48)
- **Format**: ICO
- **Purpose**: Browser tab icon

### 2. favicon-16x16.png
- **Size**: 16x16px
- **Format**: PNG
- **Purpose**: Small favicon for older browsers

### 3. favicon-32x32.png
- **Size**: 32x32px
- **Format**: PNG
- **Purpose**: Standard favicon

### 4. apple-touch-icon.png
- **Size**: 180x180px
- **Format**: PNG
- **Purpose**: iOS home screen icon

### 5. og-image.png
- **Size**: 1200x630px
- **Format**: PNG or JPG
- **Purpose**: Open Graph preview image for social media sharing
- **Note**: Should include NeuroNote branding/logo and tagline

### 6. android-chrome-192x192.png
- **Size**: 192x192px
- **Format**: PNG
- **Purpose**: Android home screen icon (standard)

### 7. android-chrome-512x512.png
- **Size**: 512x512px
- **Format**: PNG
- **Purpose**: Android home screen icon (high-res)

## Design Guidelines

- **Color scheme**: Match brand colors (primary: #3b4f41)
- **Style**: Clean, modern, recognizable at small sizes
- **Icon concept**: Consider brain/neuron imagery or interconnected nodes
- **Background**: Transparent for all PNG files

## Tools for Generation

- [Favicon.io](https://favicon.io/) - Generate from text, image, or emoji
- [RealFaviconGenerator](https://realfavicongenerator.net/) - Comprehensive favicon generator
- Figma/Sketch - Design custom icons
- ImageMagick - Batch convert and resize

## Quick Generation Commands

If you have a source logo (e.g., logo.png):

```bash
# Generate favicons with ImageMagick
convert logo.png -resize 32x32 favicon-32x32.png
convert logo.png -resize 16x16 favicon-16x16.png
convert logo.png -resize 180x180 apple-touch-icon.png
convert logo.png -resize 192x192 android-chrome-192x192.png
convert logo.png -resize 512x512 android-chrome-512x512.png

# Create ICO with multiple sizes
convert logo.png -resize 16x16 -resize 32x32 -resize 48x48 favicon.ico
```

## Verification

After adding assets, verify:
1. Favicon appears in browser tab
2. Social preview shows correctly (use Twitter Card Validator, Facebook Debugger)
3. PWA manifest loads correctly in DevTools > Application
4. All referenced files return 200 status codes
