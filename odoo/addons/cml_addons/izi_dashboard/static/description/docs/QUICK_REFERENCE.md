# Scorecard Basic - Quick Reference

## Available Options at a Glance

### Background Colors (7 options)
```
🟤 default    White background (default)
🔵 primary    Blue gradient
🟢 success    Green gradient  
🔴 danger     Red gradient
🟠 warning    Orange gradient
🔷 info       Cyan gradient
⬛ dark       Dark gray gradient
```

### Icon Types (30+ available)
```
none                 ← No icon (default)
fa-arrow-up          ↑ Growth / Increase
fa-arrow-down        ↓ Decline / Decrease
fa-line-chart        📈 Trending
fa-money             💰 Revenue
fa-dollar            $ Currency
fa-credit-card       💳 Payment
fa-shopping-cart     🛒 Orders
fa-shopping-bag      🛍️  Sales
fa-barcode           📦 Products
fa-users             👥 Customers
fa-user              👤 Single Person
fa-group             👫 Team
fa-inbox             📥 Inventory
fa-cubes             📦 Stock
fa-truck             🚚 Shipping
fa-plane             ✈️  Air Shipping
fa-ship              🚢 Sea Shipping
fa-bar-chart         📊 Analysis
fa-pie-chart         🥧 Distribution
fa-area-chart        📈 Trends
fa-check-circle      ✓ Success
fa-times-circle      ✗ Error
fa-warning           ⚠️  Alert
fa-info-circle       ℹ️  Info
fa-thumbs-up         👍 Approval
+ 600+ more from Font Awesome!
```

### Icon Colors (5 options)
```
primary    Blue   (Default)
success    Green
danger     Red
warning    Orange
info       Cyan
```

---

## Configuration Reference

| Setting | Options | Default |
|---------|---------|---------|
| **Background Color** | 7 colors | default |
| **Icon Type** | 30+ icons | none |
| **Icon Color** | 5 colors | primary |

---

## Common Use Cases

### Sales KPI
- **Background:** primary (Blue)
- **Icon:** fa-shopping-cart
- **Icon Color:** primary
- **Result:** 🔵 Blue card with shopping cart

### Revenue Tracking
- **Background:** primary (Blue)
- **Icon:** fa-money
- **Icon Color:** primary
- **Result:** 💵 Blue card with money icon

### Growth Metric
- **Background:** success (Green)
- **Icon:** fa-arrow-up
- **Icon Color:** success
- **Result:** 📈 Green card with upward trend

### Warning Alert
- **Background:** warning (Orange)
- **Icon:** fa-warning
- **Icon Color:** warning
- **Result:** ⚠️ Orange card with warning icon

### Error/Critical
- **Background:** danger (Red)
- **Icon:** fa-times-circle
- **Icon Color:** danger
- **Result:** 📉 Red card with X icon

### Employee Count
- **Background:** info (Cyan)
- **Icon:** fa-users
- **Icon Color:** info
- **Result:** 👥 Cyan card with users icon

---

## How to Configure

### Step 1: Edit Scorecard
```
1. Click scorecard on dashboard
2. Right-click → "Edit" or click settings icon
3. Open configuration panel
```

### Step 2: Select Options
```
4. Find "Background Color" → Select from dropdown
5. Find "Icon Type" → Select from dropdown
6. Find "Icon Color" → Select from dropdown
```

### Step 3: Save
```
7. Changes apply instantly
8. Save dashboard to persist changes
```

---

## Browser Support

✅ Chrome/Edge - Full support
✅ Firefox - Full support
✅ Safari - Full support
❌ IE 11 - Font Awesome not supported

---

## Default Configurations

If no configuration is set:
- **Background:** White (default)
- **Icon:** None (default)
- **Icon Color:** Primary Blue (default)

This ensures backward compatibility with existing scorecards.

---

## Pro Tips

1. **Consistency** - Use same colors across related metrics
   - Revenue: Blue cards
   - Growth: Green cards
   - Alerts: Red cards

2. **Visual Hierarchy** - More important KPIs use bolder colors
   - Primary/Success for key metrics
   - Warning/Danger for alerts only

3. **Icon Meaning** - Choose icons that represent the metric
   - Revenue → Money icon
   - Growth → Arrow Up
   - Users → People icon

4. **Dashboard Theme** - Coordinate with overall dashboard theme
   - Light theme → Use lighter backgrounds (default, info)
   - Dark theme → Use darker backgrounds (primary, dark)

5. **Mobile Friendly** - Large icons are visible on small screens
   - 32px icons fit well in scorecard
   - Circular background provides touch target

---

## Custom Icon Examples

For icons not in the dropdown, enter the Font Awesome name:

```
fa-building          Company / Organization
fa-calendar          Dates / Appointments
fa-clock             Time / Duration
fa-star              Ratings / Quality
fa-bell              Notifications
fa-envelope          Emails / Messages
fa-database          Data / Storage
fa-gear              Settings
fa-lightbulb-o       Ideas / Insights
fa-rocket            Growth / Launch
fa-lock              Security / Locked
fa-key               Access / Permissions
fa-leaf              Eco / Green
fa-heart             Favorites / Loved
fa-globe             Global / International
fa-home              Dashboard / Home
```

Find all 600+ icons at: **http://fontawesome.io/icons/**

---

## Quick Troubleshooting

| Issue | Solution |
|-------|----------|
| Options don't appear | Clear browser cache, reload page |
| Icon not showing | Verify icon name is correct at fontawesome.io |
| Colors look wrong | Check CSS file loaded correctly |
| Changes not saving | Ensure dashboard save button clicked |
| Analysis won't edit | Clear cache, should be fixed (Select2 bug resolved) |

---

**Last Updated:** 2025-11-14
**Version:** 2.0 (Font Awesome)
**Status:** Production Ready ✅
