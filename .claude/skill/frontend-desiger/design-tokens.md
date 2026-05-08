# Design Tokens Reference — Expense / Fintech SaaS

## Colour Palettes

### Option A — Dark Premium (recommended for dashboards)
```css
--color-bg-base: #0F1117;
--color-bg-surface: #1A1D27;
--color-bg-elevated: #222536;
--color-border: #2E3147;
--color-text-primary: #F0F2FF;
--color-text-secondary: #8B90A7;
--color-text-muted: #545870;
--color-accent-primary: #6C7BFF;   /* indigo-violet */
--color-accent-glow: rgba(108,123,255,0.15);
--color-success: #34D399;
--color-danger: #F87171;
--color-warning: #FBBF24;
```

### Option B — Light Clean (good for mobile-first apps)
```css
--color-bg-base: #F8F9FC;
--color-bg-surface: #FFFFFF;
--color-bg-elevated: #FFFFFF;
--color-border: #E4E7EF;
--color-text-primary: #111827;
--color-text-secondary: #6B7280;
--color-text-muted: #9CA3AF;
--color-accent-primary: #3B5BDB;   /* deep blue */
--color-accent-light: #EEF2FF;
--color-success: #059669;
--color-danger: #DC2626;
--color-warning: #D97706;
```

### Option C — Warm Neutral (softer, approachable)
```css
--color-bg-base: #FAFAF8;
--color-bg-surface: #FFFFFF;
--color-border: #E8E4DC;
--color-text-primary: #1C1917;
--color-text-secondary: #78716C;
--color-accent-primary: #EA580C;   /* warm orange */
--color-success: #16A34A;
--color-danger: #DC2626;
```

---

## Typography Scales

### Scale — Dashboard (tighter, data-dense)
```
Display:    2.25rem / 700 / -0.02em   (page titles)
Heading 1:  1.5rem  / 600 / -0.01em
Heading 2:  1.125rem / 600 / 0
Body:       0.875rem / 400 / 0.01em
Small:      0.75rem  / 400 / 0.02em
Label:      0.6875rem / 500 / 0.06em uppercase
```

### Recommended font pairings (avoid Inter/Roboto/Arial):
- **Geist** (display) + **Geist Mono** (numbers/data) — modern, technical
- **DM Sans** (headings) + **DM Mono** (data) — clean, friendly
- **Outfit** (headings) + **IBM Plex Sans** (body) — SaaS-grade
- **Plus Jakarta Sans** (all) — premium feel, underused

---

## Spacing System (Tailwind-aligned)
```
2px  → space-0.5  (hairline separators)
4px  → space-1    (tight icon gaps)
8px  → space-2    (label-to-input)
12px → space-3    (within cards)
16px → space-4    (standard padding)
24px → space-6    (card padding)
32px → space-8    (section gaps)
48px → space-12   (major section breaks)
64px → space-16   (page-level spacing)
```

---

## Shadow System
```css
--shadow-sm:  0 1px 2px rgba(0,0,0,0.08);
--shadow-md:  0 4px 12px rgba(0,0,0,0.10);
--shadow-lg:  0 8px 32px rgba(0,0,0,0.14);
--shadow-card: 0 2px 8px rgba(0,0,0,0.06), 0 0 0 1px rgba(0,0,0,0.04);
--shadow-focus: 0 0 0 3px rgba(108,123,255,0.25);  /* match accent */
```

---

## Border Radius System
```
Chips/tags:   9999px (pill)
Buttons:      8px
Inputs:       8px
Cards:        12px
Modal:        16px
Large panels: 20px
```