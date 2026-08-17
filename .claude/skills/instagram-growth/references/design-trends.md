# Carousel Visual Design Patterns for Data/Stats Content

Research pass: 2026-08-17. Directly informs the master Canva template (see `instagram-carousel` skill).

## 1. Layout

- Sweet spot: 5-7 slides for data-reveal carousels (8-10 for broader educational content, but tighter is better for a single trend signal).
- Structure: hook slide (1) → data-reveal slides (2 to n-1, one key stat each) → closing/CTA slide (last).
- Visual consistency (same grid, fonts, colors across every slide) reads as professional; inconsistency reads as unpolished and hurts swipe-through.

## 2. Typography

- Headline ~60-90px equivalent, section headers ~40-55px, body ~28-36px minimum — this is a phone-screen medium; what's readable on a monitor is illegible on a 6" screen.
- 1-2 font families max. Clean geometric sans-serif reads as credible/machine-generated-precise; hand-drawn or script fonts measurably undermine trust for data content.
- Size-jump ratio of ~1.8-2.4x between headline and body keeps hierarchy legible at a glance.

## 3. Color

- Dark editorial backgrounds with a single bright accent color outperform bright/playful "inspirational quote" palettes for a credibility-first brand — matches TrendRadar's existing dark navy/teal look.
- Use grey/muted tones for secondary elements so the one accent color reads as *meaningful* (data highlight), not decorative.
- Limit total palette to a handful of colors to avoid cognitive overload.

## 4. Genuine data vs. decoration

- Bar/line charts read as more transparent than stylized infographics.
- Visible source citation (small, present on every data slide) is a strong trust signal — its absence is noticed, not just neutral.
- Avoid "chartjunk" — decorative elements with no informational value dilute credibility rather than adding polish.

## 5. Common mistakes to avoid

- Too much text per slide — one idea per slide, not a paragraph.
- Weak slide-1 hook — a boring cover slide loses the swipe before it starts.
- Inconsistent fonts/colors/layout slide-to-slide.
- Low contrast or sub-24pt text — untestable on an actual phone before shipping is the #1 avoidable failure mode.

## Application to the master template

The existing TrendRadar look (dark navy-teal gradient, single bright teal accent, globe+wordmark lockup, thin divider lines, two-column footer) already matches this research well — it was locked in as the master template on 2026-08-17 rather than redesigned from scratch. See `instagram-carousel/SKILL.md` for the exact element structure.
