---
name: Neon Syndicate
colors:
  surface: '#131313'
  surface-dim: '#131313'
  surface-bright: '#393939'
  surface-container-lowest: '#0e0e0e'
  surface-container-low: '#1c1b1b'
  surface-container: '#201f1f'
  surface-container-high: '#2a2a2a'
  surface-container-highest: '#353534'
  on-surface: '#e5e2e1'
  on-surface-variant: '#c4c9ac'
  inverse-surface: '#e5e2e1'
  inverse-on-surface: '#313030'
  outline: '#8e9379'
  outline-variant: '#444933'
  surface-tint: '#abd600'
  primary: '#ffffff'
  on-primary: '#283500'
  primary-container: '#c3f400'
  on-primary-container: '#556d00'
  inverse-primary: '#506600'
  secondary: '#ffabf3'
  on-secondary: '#5b005b'
  secondary-container: '#fe00fe'
  on-secondary-container: '#500050'
  tertiary: '#ffffff'
  on-tertiary: '#323200'
  tertiary-container: '#eaea00'
  on-tertiary-container: '#686800'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#c3f400'
  primary-fixed-dim: '#abd600'
  on-primary-fixed: '#161e00'
  on-primary-fixed-variant: '#3c4d00'
  secondary-fixed: '#ffd7f5'
  secondary-fixed-dim: '#ffabf3'
  on-secondary-fixed: '#380038'
  on-secondary-fixed-variant: '#810081'
  tertiary-fixed: '#eaea00'
  tertiary-fixed-dim: '#cdcd00'
  on-tertiary-fixed: '#1d1d00'
  on-tertiary-fixed-variant: '#494900'
  background: '#131313'
  on-background: '#e5e2e1'
  surface-variant: '#353534'
typography:
  display-lg:
    fontFamily: Space Grotesk
    fontSize: 72px
    fontWeight: '700'
    lineHeight: '1.1'
    letterSpacing: -0.04em
  headline-lg:
    fontFamily: Space Grotesk
    fontSize: 40px
    fontWeight: '700'
    lineHeight: '1.2'
    letterSpacing: -0.02em
  headline-lg-mobile:
    fontFamily: Space Grotesk
    fontSize: 32px
    fontWeight: '700'
    lineHeight: '1.2'
    letterSpacing: -0.02em
  title-md:
    fontFamily: Space Grotesk
    fontSize: 24px
    fontWeight: '600'
    lineHeight: '1.4'
    letterSpacing: 0.02em
  body-lg:
    fontFamily: Geist
    fontSize: 18px
    fontWeight: '400'
    lineHeight: '1.6'
  body-md:
    fontFamily: Geist
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.6'
  label-mono:
    fontFamily: JetBrains Mono
    fontSize: 14px
    fontWeight: '500'
    lineHeight: '1.2'
    letterSpacing: 0.1em
spacing:
  unit: 4px
  gutter: 24px
  margin-mobile: 16px
  margin-desktop: 64px
  container-max: 1440px
---

## Brand & Style

This design system is built on a "High-Voltage Retro-Futurism" aesthetic. It targets a tech-savvy, high-energy audience that values intensity, speed, and a rebellious digital identity. The style is a hybrid of **Cyber-Brutalism** and **Vaporwave-influenced Glassmorphism**, characterized by extreme contrast, vibrant light-emissive properties, and sharp structural integrity.

The UI should feel like a high-end terminal interface from a dystopian future. Every element must appear as if it is powered by electricity, using pure black backgrounds to make neon accents pop with maximum luminance.

## Colors

The palette is anchored in **Pure Black (#000000)** to provide an infinite depth for the emissive accents. 

- **Primary (Cyber Lime):** Use for primary actions and critical status indicators.
- **Secondary (Hot Pink):** Use for secondary interactive elements and decorative highlights.
- **Tertiary (Acid Yellow):** Use for warnings, secondary data points, and tactical accents.
- **Neutral (Dark Charcoal):** Specifically for surface containers to distinguish interactive zones from the void background.

All colors should be applied with an "on-state" glow. When an element is active, it should utilize a 0.5 opacity tint of its own hex value for surrounding drop-shadows to simulate light pollution on the black canvas.

## Typography

The typography strategy focuses on precision and mechanical clarity. 

- **Display & Headlines:** Use **Space Grotesk**. Its geometric quirks and sharp terminals reinforce the futuristic vibe. 
- **Body Text:** Use **Geist** for its exceptional legibility and developer-centric aesthetic. It maintains a clean, neutral balance against the aggressive headlines.
- **Utility & Data:** Use **JetBrains Mono** for all labels, buttons, and micro-copy. This adds a "coded" feel to the interface, suggesting high-tech functionality.

Text should rarely be pure white; use a high-brightness version of the accent colors for headlines, or a 90% silver-gray for long-form body text.

## Layout & Spacing

The layout follows a **Rigid Tactical Grid**. Content is housed within structured modules that align to a 4px baseline.

- **Desktop:** 12-column grid with wide 64px margins to create a "letterboxed" cinematic feel.
- **Tablet:** 8-column grid with 32px margins.
- **Mobile:** 4-column grid with 16px margins.

Spacing should be aggressive and mathematical. Avoid soft or organic padding; use generous white space (or "black space") to isolate components, making the neon borders feel more impactful.

## Elevation & Depth

Depth is not created through shadows, but through **Luminance and Layering**.

1. **Background:** Level 0, Pure Black.
2. **Surfaces:** Level 1, Dark Charcoal (#121212) with 1px solid neon borders.
3. **Overlays:** Level 2, Dark Charcoal with backdrop-blur (12px) and a higher intensity glow on the border.

Instead of traditional drop shadows, use **Outer Glows**. A `0px 0px 8px` blur using the primary or secondary color should be applied to active borders and text buttons to simulate light emission.

## Shapes

The shape language is strictly **Sharp (0px roundedness)**. 

To evoke a high-tech, aggressive feel, avoid all curves. Use 45-degree "clipped corners" (chamfers) for large container elements and buttons to mimic military-grade hardware or circuit board paths. 1px borders are mandatory for all container elements to define their boundaries against the black background.

## Components

### Buttons
- **Primary:** Solid Cyber Lime background with Black text. No shadow, but a strong 4px lime glow on hover.
- **Secondary:** Transparent background, 1px Hot Pink border, Hot Pink text.
- **Ghost:** JetBrains Mono text with ">>" prefix.

### Cards & Containers
- Always #121212 background.
- 1px border using a gradient (e.g., Cyber Lime to Acid Yellow).
- Optional: A "scanline" overlay pattern (0.05 opacity) to add texture.

### Input Fields
- Underline-only or 1px border. 
- Focus state: Border color changes to Acid Yellow with a pulsing glow effect.
- Cursor: Block-style (non-blinking or fast-blink).

### Status Indicators
- Use Cyber Lime for "System Clear", Hot Pink for "Override/Action Required", and Acid Yellow for "Warning/Data Stream".

### Additional Elements
- **Data Glitch:** Occasional 1px horizontal offsets for hover states on decorative elements.
- **Terminals:** Use JetBrains Mono in a scrollable container for log outputs or technical specs.