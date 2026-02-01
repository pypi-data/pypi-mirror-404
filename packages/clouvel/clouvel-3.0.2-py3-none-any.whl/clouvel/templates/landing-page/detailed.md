# {PROJECT_NAME} Landing Page PRD

> This document is law. If it's not here, don't build it. If it's here, you MUST build it.
>
> Created: {DATE}
> Version: 1.0

---

## 1. One-line Summary

**[Product/Service]** landing page for **[Goal Action]**

Example: "SaaS product landing page for early bird signup conversion"

---

## 2. Core Principles

> 3 rules that never change. Everything follows these.

1. **[Principle 1]**: e.g., "Mobile-first, desktop-enhanced"
2. **[Principle 2]**: e.g., "One clear CTA per viewport"
3. **[Principle 3]**: e.g., "Load under 3 seconds on 3G"

---

## 3. Goal Definition

### 3.1 Business Goals

| Metric | Target | Measurement | Priority |
|--------|--------|-------------|----------|
| Conversion Rate | > 5% | GA4 goal tracking | P0 |
| Bounce Rate | < 40% | GA4 | P0 |
| Time on Page | > 2 min | GA4 | P1 |
| Scroll Depth | > 75% | Custom event | P1 |
| Email Captures | > X/week | CRM | P0 |

### 3.2 User Action Goals

| Priority | Action | Trigger | Success Metric |
|----------|--------|---------|----------------|
| Primary | [e.g., Sign up for early access] | CTA button click | Form submission |
| Secondary | [e.g., Watch demo video] | Play button | Video 50%+ watched |
| Tertiary | [e.g., Share on social] | Share buttons | Click + share complete |

### 3.3 Conversion Funnel

```
Visit → Scroll → Engage → Click CTA → Submit Form → Confirm
  │        │        │         │            │           │
  │        │        │         │            │           └─ Thank you page
  │        │        │         │            └─ Form validation
  │        │        │         └─ CTA visibility (> 2s in viewport)
  │        │        └─ Interactive element clicked
  │        └─ Passed fold (hero section)
  └─ Page loaded
```

---

## 4. Target Visitors

### 4.1 Primary Visitor Persona

| Attribute | Value |
|-----------|-------|
| Who | [e.g., Startup founders, age 25-45] |
| Traffic Source | [e.g., Twitter, Product Hunt, Google] |
| Device | [e.g., 60% mobile, 40% desktop] |
| Intent | [e.g., Looking for productivity tools] |
| Decision Time | [e.g., < 5 minutes to decide] |

### 4.2 Visitor Journey Stages

| Stage | Characteristics | Content Needed | CTA |
|-------|-----------------|----------------|-----|
| Awareness | First time hearing about product | Problem + Solution | Learn more |
| Interest | Comparing options | Features + Benefits | See demo |
| Decision | Ready to try | Pricing + Social proof | Sign up |

### 4.3 Aha Moment

> The moment visitor decides to convert. Must happen before scroll to CTA.

**Trigger**: [What they see/read]
**Realization**: [What they understand]
**Time to Aha**: < X seconds from landing

Example: "Visitor reads headline → sees '10x faster' claim → watches 15s demo GIF → realizes this solves their exact problem"

---

## 5. Page Structure

### P0 (Must Have) - No launch without these

#### Section: Hero

**Purpose**: Capture attention, communicate value proposition, drive primary CTA

**Layout Specification**:
```
+------------------------------------------+
|           [Navigation Bar]                |
|  Logo                    [CTA Button]     |
+------------------------------------------+
|                                           |
|     [Headline - max 10 words]             |
|                                           |
|     [Subheadline - max 25 words]          |
|                                           |
|     [Primary CTA Button]                  |
|     [Secondary CTA - text link]           |
|                                           |
|     [Hero Image / Demo GIF / Video]       |
|                                           |
+------------------------------------------+

Desktop: 2-column (text left, visual right)
Mobile: Single column (text → visual → CTA)
Height: 100vh (min 600px)
```

**Content Specification**:
```typescript
interface HeroContent {
  headline: {
    text: string;      // Max 10 words
    emphasis: string;  // Word(s) to highlight
  };
  subheadline: {
    text: string;      // Max 25 words
    focusOn: 'benefit' | 'method' | 'result';
  };
  primaryCTA: {
    text: string;      // Max 4 words, action verb
    href: string;
    trackingId: string;
  };
  secondaryCTA?: {
    text: string;
    href: string;
  };
  visual: {
    type: 'image' | 'gif' | 'video';
    src: string;
    alt: string;
    autoplay?: boolean;  // For video/gif
  };
}
```

**Test Scenarios**:
- [ ] Headline readable in < 3 seconds
- [ ] CTA visible without scroll (above fold)
- [ ] Visual loads within 2 seconds
- [ ] Mobile: CTA accessible with thumb

---

#### Section: Problem

**Purpose**: Build empathy, acknowledge pain points

**Layout Specification**:
```
+------------------------------------------+
|                                           |
|     [Section Title]                       |
|                                           |
|  +----------+  +----------+  +----------+ |
|  | Pain 1   |  | Pain 2   |  | Pain 3   | |
|  | [Icon]   |  | [Icon]   |  | [Icon]   | |
|  | [Text]   |  | [Text]   |  | [Text]   | |
|  +----------+  +----------+  +----------+ |
|                                           |
+------------------------------------------+

Desktop: 3-column grid
Mobile: Vertical stack
```

**Content Specification**:
```typescript
interface ProblemSection {
  title: string;  // e.g., "Sound familiar?"
  painPoints: Array<{
    icon: string;
    title: string;      // Max 5 words
    description: string; // Max 20 words
    emotionalHook: string; // The frustration
  }>;  // Exactly 3 items
}
```

---

#### Section: Solution

**Purpose**: Present product as the answer

**Layout Specification**:
```
+------------------------------------------+
|                                           |
|     [Section Title]                       |
|     [Section Subtitle]                    |
|                                           |
|     [Product Screenshot / Demo]           |
|                                           |
|     [Key differentiator statement]        |
|                                           |
+------------------------------------------+
```

---

#### Section: Features

**Purpose**: Showcase capabilities

**Layout Specification**:
```
+------------------------------------------+
|                                           |
|     [Section Title]                       |
|                                           |
|  +------------------+  +----------------+ |
|  | Feature 1        |  | Feature 2      | |
|  | [Visual]         |  | [Visual]       | |
|  | [Title]          |  | [Title]        | |
|  | [Description]    |  | [Description]  | |
|  | [Benefit]        |  | [Benefit]      | |
|  +------------------+  +----------------+ |
|                                           |
|  +------------------+  +----------------+ |
|  | Feature 3        |  | Feature 4      | |
|  +------------------+  +----------------+ |
|                                           |
+------------------------------------------+

Features: 3-6 items (4 recommended)
```

**Content Specification**:
```typescript
interface Feature {
  icon: string;
  title: string;        // What it is
  description: string;  // How it works
  benefit: string;      // Why it matters
  visual?: string;      // Screenshot or demo
}
```

---

#### Section: CTA (Mid-page)

**Purpose**: Capture users ready to convert before reaching bottom

**Layout**:
```
+------------------------------------------+
|  [Colored background - contrast]          |
|                                           |
|     [Reinforcement headline]              |
|     [Primary CTA Button]                  |
|     [Trust badge or micro-copy]           |
|                                           |
+------------------------------------------+
```

---

#### Section: Footer

**Purpose**: Trust, navigation, legal

**Layout**:
```
+------------------------------------------+
|  Logo    | Links        | Social  | Legal |
|          | About        | Twitter | Privacy|
|          | Contact      | GitHub  | Terms  |
|          | Blog         |         |        |
+------------------------------------------+
|  © 2024 Company Name                      |
+------------------------------------------+
```

---

### P1 (Should Have)

#### Section: Social Proof

**Purpose**: Build trust through validation

**Types**:
```typescript
type SocialProofType =
  | 'testimonials'    // User quotes with photos
  | 'logos'           // Company logos using product
  | 'stats'           // Numbers (users, revenue, etc.)
  | 'ratings'         // Star ratings, review scores
  | 'media'           // "As seen in" logos
```

**Layout Options**:
```
Option A: Logo Wall
+------------------------------------------+
| "Trusted by"                              |
| [Logo] [Logo] [Logo] [Logo] [Logo]       |
+------------------------------------------+

Option B: Testimonial Carousel
+------------------------------------------+
| "[Quote]"                                 |
| - Name, Title @ Company                   |
| [Photo]                                   |
| [< Prev] [• • •] [Next >]                |
+------------------------------------------+

Option C: Stats Bar
+------------------------------------------+
| 10,000+    |    99.9%    |    4.9★      |
| Users      |    Uptime   |    Rating    |
+------------------------------------------+
```

---

#### Section: Pricing

**Purpose**: Show value, reduce friction

**Layout**:
```
+------------------------------------------+
|                                           |
|     "Simple, transparent pricing"         |
|                                           |
|  +--------+  +--------+  +--------+      |
|  | Free   |  | Pro    |  | Team   |      |
|  | $0     |  | $X/mo  |  | $Y/mo  |      |
|  | [List] |  | [List] |  | [List] |      |
|  | [CTA]  |  | [CTA]  |  | [CTA]  |      |
|  +--------+  +--------+  +--------+      |
|                                           |
+------------------------------------------+
```

**Content Specification**:
```typescript
interface PricingTier {
  name: string;
  price: {
    amount: number;
    period: 'month' | 'year' | 'once';
    currency: string;
    originalPrice?: number;  // For strikethrough
  };
  description: string;
  features: string[];        // Bullet points
  cta: {
    text: string;
    href: string;
    highlighted: boolean;
  };
  badge?: string;  // e.g., "Most Popular", "Best Value"
}
```

---

#### Section: FAQ

**Purpose**: Address objections, reduce support load

**Layout**:
```
+------------------------------------------+
|     "Frequently Asked Questions"          |
|                                           |
|  [+] Question 1?                          |
|  [-] Question 2?                          |
|      Answer to question 2...              |
|  [+] Question 3?                          |
|                                           |
+------------------------------------------+

Behavior: Accordion (one open at a time)
```

---

### P2 (Nice to Have)

| Section | Purpose | Notes |
|---------|---------|-------|
| Demo | Interactive experience | Video or live demo |
| Comparison | vs. competitors | Table format |
| Integrations | Ecosystem | Logo grid |
| Roadmap | Future vision | Timeline |

---

## 6. Constraints (AI Boundaries)

### ALWAYS (Must Execute)
- [ ] Mobile responsive (320px - 1440px)
- [ ] CTA buttons clearly visible with high contrast
- [ ] Page load < 3 seconds (LCP)
- [ ] Clear value proposition in hero
- [ ] Semantic HTML for accessibility
- [ ] All images have alt text
- [ ] Form validation with helpful errors

### ASK FIRST (Confirm Before)
- [ ] Adding external scripts
- [ ] Adding new sections
- [ ] Changing form fields
- [ ] Adding modals or popups
- [ ] Changing CTA text

### NEVER (Absolutely Forbidden)
- [ ] **Add sections not in this spec**
- [ ] Auto-playing video with sound
- [ ] Popups on page load
- [ ] Fake testimonials or stats
- [ ] Heavy animations that hurt performance
- [ ] Dark patterns (hidden opt-outs, confusing UX)
- [ ] Third-party trackers without consent

### Out of Scope
- Blog section - Reason: Separate page
- Multi-language - Reason: v2
- User accounts - Reason: Separate app

---

## 7. Copywriting Specification

### 7.1 Tone & Voice

| Attribute | Value | Example |
|-----------|-------|---------|
| Tone | [Friendly / Professional / Bold] | [Example sentence] |
| Voice | [1st person / 2nd person / 3rd person] | "We help you..." / "You'll love..." |
| Style | [Casual / Formal] | [해요체 / 합니다체] |
| Emotion | [Excitement / Trust / Urgency] | |

### 7.2 Copy Templates

**Headline Formula**:
```
[Result] + [Timeframe] + [Without Pain Point]

Examples:
- "Build landing pages in 10 minutes. No code required."
- "10x your productivity. Without the burnout."
```

**CTA Button Formula**:
```
[Action Verb] + [Value/Object]

Examples:
- "Start Free Trial" (not "Submit")
- "Get Early Access" (not "Sign Up")
- "See Demo" (not "Click Here")
```

**Subheadline Formula**:
```
[How it works] + [Key benefit]

Examples:
- "Drag and drop builder that converts visitors into customers."
```

### 7.3 Microcopy

| Location | Purpose | Example |
|----------|---------|---------|
| Below CTA | Reduce friction | "No credit card required" |
| Form field | Clarify input | "Enter your work email" |
| Error state | Help recover | "Please enter a valid email" |
| Success state | Confirm action | "You're in! Check your email." |

---

## 8. Design Specification

### 8.1 Color System

| Role | Color | Hex | Usage |
|------|-------|-----|-------|
| Primary | [Color name] | #XXXXXX | CTAs, links, key elements |
| Secondary | [Color name] | #XXXXXX | Accents, hover states |
| Background | [Color name] | #XXXXXX | Page background |
| Surface | [Color name] | #XXXXXX | Cards, sections |
| Text Primary | [Color name] | #XXXXXX | Headlines, body |
| Text Secondary | [Color name] | #XXXXXX | Captions, hints |
| Success | [Color name] | #XXXXXX | Confirmations |
| Error | [Color name] | #XXXXXX | Errors |

### 8.2 Typography

| Element | Font | Weight | Size (Desktop) | Size (Mobile) | Line Height |
|---------|------|--------|----------------|---------------|-------------|
| H1 | [Font] | Bold | 56px | 36px | 1.1 |
| H2 | [Font] | Semibold | 40px | 28px | 1.2 |
| H3 | [Font] | Medium | 24px | 20px | 1.3 |
| Body | [Font] | Regular | 18px | 16px | 1.6 |
| Caption | [Font] | Regular | 14px | 14px | 1.5 |

### 8.3 Spacing System

```
Base unit: 8px

xs: 4px   (0.5x)
sm: 8px   (1x)
md: 16px  (2x)
lg: 24px  (3x)
xl: 32px  (4x)
2xl: 48px (6x)
3xl: 64px (8x)
4xl: 96px (12x)

Section padding:
- Desktop: 96px vertical, 64px horizontal
- Mobile: 48px vertical, 24px horizontal
```

### 8.4 Component Specs

**Primary Button**:
```css
.btn-primary {
  background: var(--primary);
  color: white;
  padding: 16px 32px;
  border-radius: 8px;
  font-weight: 600;
  font-size: 18px;
  transition: all 0.2s;
}
.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}
```

**Secondary Button**:
```css
.btn-secondary {
  background: transparent;
  color: var(--primary);
  border: 2px solid var(--primary);
  padding: 14px 30px;
  border-radius: 8px;
}
```

**Card**:
```css
.card {
  background: var(--surface);
  border-radius: 12px;
  padding: 32px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}
```

---

## 9. Technical Specification

### 9.1 Tech Stack

| Category | Choice | Reason |
|----------|--------|--------|
| Framework | Next.js / Astro / HTML | [Reason] |
| Styling | Tailwind / CSS | [Reason] |
| Hosting | Vercel / Netlify / GitHub Pages | [Reason] |
| Analytics | GA4 / Plausible / PostHog | [Reason] |
| Forms | Native / Formspree / ConvertKit | [Reason] |
| CMS | None / Contentful / Sanity | [Reason] |

### 9.2 Performance Budget

| Metric | Target | Tool |
|--------|--------|------|
| LCP (Largest Contentful Paint) | < 2.5s | Lighthouse |
| FID (First Input Delay) | < 100ms | Lighthouse |
| CLS (Cumulative Layout Shift) | < 0.1 | Lighthouse |
| Total Page Weight | < 1MB | DevTools |
| JavaScript | < 100KB gzipped | Bundler |
| Images | WebP, lazy loaded | - |

### 9.3 Responsive Breakpoints

```css
/* Mobile first */
@media (min-width: 640px) { /* sm */ }
@media (min-width: 768px) { /* md */ }
@media (min-width: 1024px) { /* lg */ }
@media (min-width: 1280px) { /* xl */ }
```

---

## 10. SEO & Meta Tags

### 10.1 Required Meta Tags

```html
<head>
  <!-- Primary -->
  <title>{Product} - {Value Proposition} | {Brand}</title>
  <meta name="description" content="{150 chars max}">
  <meta name="keywords" content="{keyword1}, {keyword2}">

  <!-- Open Graph / Facebook -->
  <meta property="og:type" content="website">
  <meta property="og:url" content="{URL}">
  <meta property="og:title" content="{Title}">
  <meta property="og:description" content="{Description}">
  <meta property="og:image" content="{Image URL - 1200x630}">

  <!-- Twitter -->
  <meta property="twitter:card" content="summary_large_image">
  <meta property="twitter:url" content="{URL}">
  <meta property="twitter:title" content="{Title}">
  <meta property="twitter:description" content="{Description}">
  <meta property="twitter:image" content="{Image URL}">

  <!-- Favicon -->
  <link rel="icon" type="image/svg+xml" href="/favicon.svg">
  <link rel="apple-touch-icon" href="/apple-touch-icon.png">
</head>
```

### 10.2 SEO Checklist

- [ ] Semantic HTML (header, main, section, footer)
- [ ] One H1 per page
- [ ] Logical heading hierarchy (H1 > H2 > H3)
- [ ] All images have descriptive alt text
- [ ] Internal links use descriptive anchor text
- [ ] sitemap.xml generated
- [ ] robots.txt configured
- [ ] Canonical URL set
- [ ] Schema.org markup (Organization, Product)

### 10.3 Social Share Preview

| Platform | Image Size | Title Length | Description |
|----------|------------|--------------|-------------|
| Facebook | 1200x630 | 60 chars | 155 chars |
| Twitter | 1200x600 | 70 chars | 200 chars |
| LinkedIn | 1200x627 | 70 chars | 100 chars |

---

## 11. Form Specification

### 11.1 Lead Capture Form

**Fields**:
```typescript
interface LeadForm {
  email: {
    type: 'email';
    required: true;
    placeholder: 'you@company.com';
    validation: /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    errorMessage: 'Please enter a valid email';
  };
  name?: {
    type: 'text';
    required: false;
    placeholder: 'Your name';
  };
  company?: {
    type: 'text';
    required: false;
    placeholder: 'Company name';
  };
}
```

**States**:
| State | UI | Action |
|-------|-----|--------|
| Default | Input + Submit button | - |
| Focus | Highlighted border | - |
| Error | Red border + error message | Show inline error |
| Loading | Disabled + spinner | Prevent double submit |
| Success | Hide form + show confirmation | Redirect or message |

**Validation Rules**:
- Client-side validation on blur
- Server-side validation on submit
- Honeypot field for spam prevention
- Rate limiting: 3 submissions per minute per IP

---

## 12. Analytics & Tracking

### 12.1 Events to Track

| Event | Trigger | Parameters |
|-------|---------|------------|
| page_view | Page load | page_path, referrer |
| cta_click | CTA button click | button_id, location |
| form_start | First form field focus | form_id |
| form_submit | Form submission | form_id, success |
| scroll_depth | 25%, 50%, 75%, 100% | depth_percentage |
| video_play | Play button click | video_id |
| video_complete | Video ends | video_id, watch_time |
| outbound_click | External link click | destination_url |

### 12.2 Conversion Goals

| Goal | Trigger | Value |
|------|---------|-------|
| Primary Conversion | Form submission confirmed | 1.0 |
| Demo Viewed | Video 50%+ watched | 0.5 |
| High Engagement | Scroll > 75% + Time > 2min | 0.3 |

### 12.3 UTM Parameters

```
Required tracking:
?utm_source=[source]
&utm_medium=[medium]
&utm_campaign=[campaign]
&utm_content=[content]  (optional)
```

---

## 13. Edge Cases

| Situation | Expected Behavior | Test Case |
|-----------|-------------------|-----------|
| JavaScript disabled | Core content visible | Disable JS in browser |
| Slow connection (3G) | Progressive loading | Network throttle |
| Very small screen (320px) | All content accessible | iPhone SE viewport |
| Very large screen (4K) | Content max-width contained | 4K monitor |
| Form double submit | Prevent, show loading | Rapid click submit |
| Invalid email format | Inline error, focus field | Type "abc" |
| Ad blocker | Analytics graceful failure | uBlock Origin |
| Dark mode preference | Respect system preference | prefers-color-scheme |
| Keyboard navigation | Full accessibility | Tab through page |
| Screen reader | Proper announcements | VoiceOver/NVDA |

---

## 14. Performance Optimization

### 14.1 Image Optimization

```typescript
interface ImageSpec {
  format: 'webp' | 'avif' | 'png';  // WebP preferred
  loading: 'lazy' | 'eager';        // Eager for above-fold
  sizes: string;                    // Responsive sizes
  srcset: string;                   // Multiple resolutions
}

// Example
<img
  src="hero.webp"
  srcset="hero-400.webp 400w, hero-800.webp 800w, hero-1200.webp 1200w"
  sizes="(max-width: 640px) 100vw, 50vw"
  loading="eager"
  alt="Product demo"
>
```

### 14.2 Critical CSS

- Inline critical CSS for above-fold content
- Defer non-critical CSS
- Remove unused CSS (PurgeCSS)

### 14.3 JavaScript Loading

```html
<!-- Critical scripts -->
<script src="critical.js"></script>

<!-- Non-critical scripts -->
<script src="analytics.js" defer></script>
<script src="interactions.js" defer></script>
```

---

## 15. Definition of Done (DoD)

### Content DoD
- [ ] All copy reviewed and approved
- [ ] All images/assets finalized
- [ ] Legal pages linked (Privacy, Terms)
- [ ] Contact information correct

### Design DoD
- [ ] Matches design spec exactly
- [ ] All breakpoints tested
- [ ] Dark mode works (if applicable)
- [ ] Consistent spacing and typography

### Technical DoD
- [ ] Lighthouse score > 90 (all categories)
- [ ] Cross-browser tested (Chrome, Firefox, Safari)
- [ ] Forms work and data reaches destination
- [ ] Analytics tracking verified
- [ ] SSL certificate active
- [ ] 404 page exists

### Accessibility DoD
- [ ] WCAG 2.1 AA compliant
- [ ] Keyboard navigable
- [ ] Screen reader tested
- [ ] Color contrast meets standards (4.5:1)

### Launch DoD
- [ ] Domain connected
- [ ] Social preview images correct
- [ ] SEO metadata verified
- [ ] Monitoring/alerts configured
- [ ] Backup/rollback plan documented

---

## 16. A/B Testing Plan

### 16.1 Test Candidates

| Element | Variant A | Variant B | Hypothesis |
|---------|-----------|-----------|------------|
| Headline | Current | [Alternative] | B increases scroll |
| CTA text | "Get Started" | "Start Free" | B increases clicks |
| Hero image | Product shot | Demo GIF | B increases engagement |
| Social proof | Testimonials | Stats | A builds more trust |

### 16.2 Test Requirements

- Minimum sample: 1000 visitors per variant
- Statistical significance: 95%
- Test duration: 2-4 weeks
- One test at a time

---

## 17. Changelog

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| {DATE} | 1.0 | Initial draft | |
