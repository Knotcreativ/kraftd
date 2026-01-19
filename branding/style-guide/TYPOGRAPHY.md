# Kraftd Typography Guide

## Font Selection

### Primary Font: Inter
- **Classification:** Humanist Sans-serif
- **Use Cases:** Headlines, body text, UI labels
- **Advantages:** Modern, highly legible, excellent for screens
- **Fallback:** Segoe UI, -apple-system, BlinkMacSystemFont, sans-serif

### Font Weights

```css
font-weight: 400; /* Regular - body text, standard content */
font-weight: 500; /* Medium - buttons, labels, emphasis */
font-weight: 600; /* Semibold - subheadings, stronger emphasis */
font-weight: 700; /* Bold - main headings, important elements */
```

---

## Heading Hierarchy

### H1 - Page Title
```css
font-size: 32px;
font-weight: 700;
line-height: 1.2;
color: #1A1A1A;
margin-bottom: 24px;
letter-spacing: -0.5px;
```
**Use:** Main page titles, primary headlines

### H2 - Section Header
```css
font-size: 24px;
font-weight: 600;
line-height: 1.3;
color: #1A1A1A;
margin-bottom: 16px;
letter-spacing: -0.25px;
```
**Use:** Major section headings, dashboard titles

### H3 - Subsection Header
```css
font-size: 20px;
font-weight: 600;
line-height: 1.4;
color: #333333;
margin-bottom: 12px;
```
**Use:** Subsection titles, card titles

### H4 - Component Header
```css
font-size: 16px;
font-weight: 500;
line-height: 1.5;
color: #333333;
margin-bottom: 8px;
```
**Use:** Form labels, small component headers

### H5 - Minor Header
```css
font-size: 14px;
font-weight: 600;
line-height: 1.5;
color: #333333;
text-transform: uppercase;
letter-spacing: 0.5px;
margin-bottom: 8px;
```
**Use:** Badge labels, small titles

---

## Body Text

### Standard Body
```css
font-size: 16px;
font-weight: 400;
line-height: 1.6;
color: #333333;
letter-spacing: 0.2px;
```
**Use:** Primary content, paragraphs, article text

### Compact Body
```css
font-size: 14px;
font-weight: 400;
line-height: 1.6;
color: #333333;
```
**Use:** Secondary content, UI text, descriptions

### Small Text
```css
font-size: 12px;
font-weight: 400;
line-height: 1.5;
color: #757575;
```
**Use:** Captions, helper text, timestamps, footnotes

### Extra Small
```css
font-size: 11px;
font-weight: 400;
line-height: 1.4;
color: #757575;
letter-spacing: 0.3px;
```
**Use:** Labels, badges, micro-interactions

---

## Call-to-Action Text

### Primary CTA
```css
font-size: 14px;
font-weight: 500;
text-transform: uppercase;
letter-spacing: 0.5px;
color: #FFFFFF;
background-color: #00BCD4;
padding: 12px 24px;
border-radius: 4px;
```
**Example:** "Get Started", "Send Message", "Learn More"

### Secondary CTA
```css
font-size: 14px;
font-weight: 500;
color: #00BCD4;
text-decoration: none;
border-bottom: 2px solid #00BCD4;
```
**Example:** "View Details", "Explore More", "Try Demo"

---

## Link Styling

### Standard Link
```css
color: #00BCD4;
text-decoration: none;
border-bottom: 1px solid transparent;
transition: all 0.2s ease;
```

### Link Hover State
```css
color: #00838F;
border-bottom: 1px solid #00838F;
```

### Link Visited
```css
color: #0097A7;
```

---

## List Styling

### Unordered List
- Use bullet points (•) in cyan (#00BCD4)
- Consistent 24px margin-left
- 1.6 line-height for readability

### Ordered List
- Use numbers (1., 2., 3.)
- Consistent 24px margin-left
- Same line-height as unordered

### Description List
```css
dt {
  font-weight: 600;
  margin-top: 8px;
  color: #333333;
}

dd {
  margin-left: 16px;
  color: #757575;
  margin-bottom: 12px;
}
```

---

## Emphasis & Special Text

### Bold
```css
font-weight: 600;
color: #1A1A1A;
```
**Use:** Important words, key points

### Italic
```css
font-style: italic;
color: #333333;
```
**Use:** Quotes, references, cited works (sparingly)

### Code/Monospace
```css
font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
font-size: 13px;
background-color: #F5F5F5;
padding: 2px 6px;
border-radius: 3px;
color: #C13B1B;
```

### Blockquote
```css
border-left: 4px solid #00BCD4;
padding-left: 16px;
margin-left: 0;
color: #757575;
font-style: italic;
```

---

## Responsive Typography

### Desktop (1024px+)
```css
h1 { font-size: 32px; }
h2 { font-size: 24px; }
h3 { font-size: 20px; }
body { font-size: 16px; }
```

### Tablet (768px - 1023px)
```css
h1 { font-size: 28px; }
h2 { font-size: 20px; }
h3 { font-size: 18px; }
body { font-size: 15px; }
```

### Mobile (< 768px)
```css
h1 { font-size: 24px; }
h2 { font-size: 18px; }
h3 { font-size: 16px; }
body { font-size: 14px; }
```

---

## Spacing Guidelines

### Margin Bottom (Headlines)
- H1: 24px
- H2: 20px
- H3: 16px
- H4: 12px
- H5: 8px

### Paragraph Spacing
- Between paragraphs: 16px
- First paragraph: no top margin
- Last paragraph: no bottom margin

### Line Height
- Headings: 1.2 - 1.4
- Body text: 1.6
- Code blocks: 1.5

---

## Color Usage

### Primary Text
- **Color:** #1A1A1A (nearly black)
- **Use:** Headings, important text
- **Contrast:** 21:1 on white (WCAG AAA)

### Secondary Text
- **Color:** #333333
- **Use:** Body text, secondary content
- **Contrast:** 12.6:1 on white (WCAG AAA)

### Tertiary Text
- **Color:** #757575
- **Use:** Help text, captions, disabled states
- **Contrast:** 4.54:1 on white (WCAG AA)

### Link Text
- **Color:** #00BCD4 (cyan)
- **Use:** Links, interactive elements
- **Contrast:** 4.5:1 on white (WCAG AA)

---

## Best Practices

✅ **Do:**
- Maintain consistent line-height (1.6 for body)
- Use adequate spacing between text blocks
- Keep line length between 50-75 characters
- Use hierarchy to guide readers
- Ensure sufficient contrast ratios
- Use different font weights sparingly
- Align text to left by default

❌ **Don't:**
- Justify text (except in special cases)
- Use all caps for large blocks of text
- Combine multiple font families
- Mix serif and sans-serif without purpose
- Use light text on light backgrounds
- Underline text (unless it's a link)
- Use more than 3 font weights on one page

---

**Version:** 1.0  
**Last Updated:** January 19, 2026
