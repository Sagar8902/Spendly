# Component Patterns — Expense Tracker / Fintech SaaS

## Stat Cards (KPI tiles)
Best practices:
- Show: metric label, current value, period-over-period delta (with colour + arrow icon)
- Subtle background gradient or top-border accent to differentiate card type
- Never show more than 4 stat cards in a single row on desktop
- Mobile: 2 columns, or horizontal scroll strip

```jsx
// Pattern:
<StatCard
  label="Total Spent"
  value="₹24,850"
  delta="+12.4%"
  deltaDirection="up"      // "up" | "down" | "neutral"
  deltaSentiment="bad"     // spending up = bad; income up = good
  period="vs last month"
  icon={<SpendIcon />}
/>
```

---

## Transaction List / Table
Best practices:
- Use a list (not a full data table) for <50 items; table for paginated larger sets
- Each row: category icon + colour dot, merchant name, date, amount (right-aligned)
- Amount colour: red for expenses, green for income, muted for transfers
- Hover state: subtle bg highlight, show quick-action icons (edit, delete)
- Group by date if showing multiple days
- Skeleton loading states — never blank screen while fetching

---

## Category Tags / Chips
```jsx
// Colour-coded, pill-shaped
<CategoryTag category="Food" />   // maps to pre-defined colour
```
Palette suggestion (map to Tailwind bg/text):
```
Food & Drink  → amber
Transport     → blue
Shopping      → purple
Health        → green
Entertainment → pink
Bills         → slate
Income        → emerald
```

---

## Charts (for Recharts / Chart.js)
- **Spending over time**: Area chart with gradient fill, no gridlines on y-axis
- **Category breakdown**: Donut chart (not pie) with legend below
- **Budget vs actual**: Horizontal bar pairs or progress bars per category
- Tooltips: custom styled, match app theme — never browser defaults
- Axis labels: muted colour, small font, minimal tick count
- Animate on mount with `animationBegin={0}` and short `animationDuration`

---

## Empty States
Every list/table needs an empty state:
- Centered layout: illustration (SVG) + headline + subtext + CTA button
- Keep illustrations simple (line-style, match accent colour)
- Examples: "No transactions yet", "Add your first expense to get started"

---

## Forms (Add Expense / Edit)
- Use bottom sheet / slide-over panel on mobile, modal on desktop
- Field order: Amount → Category → Date → Note (most important first)
- Amount input: large font, numeric keyboard on mobile
- Date: default to today, easy +/-1 day navigation
- Category: visual grid of icon+label chips, not a dropdown
- Submit button: full-width on mobile, right-aligned on desktop
- Inline validation: show errors on blur, not on submit

---

## Navigation Patterns
- **Mobile**: Bottom tab bar (5 items max) with active indicator
- **Desktop**: Left sidebar (collapsible), 240px expanded / 64px icon-only collapsed
- Active state: accent bg pill or left border indicator — never just bold text
- Sidebar sections: group logically (Overview, Transactions, Budgets, Reports, Settings)

---

## Loading / Skeleton States
```jsx
// Card skeleton pattern (Tailwind):
<div className="animate-pulse space-y-3">
  <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4" />
  <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-1/2" />
</div>
```
Rules:
- Match skeleton shape to actual content (same height/width proportions)
- Use shimmer animation (translate-x sweep) for premium feel
- Never show spinner alone for content areas — use skeletons

---

## Date Range Picker
- Show preset options first: Today, This week, This month, Last month, Custom
- Custom: inline calendar, not a modal
- Always show selected range as a readable string: "May 1 – May 8, 2026"