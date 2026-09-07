# Scorecard Basic Customization - Implementation Guide

## Overview
Added custom background colors and Font Awesome icon customization to the `scrcard_basic` visual type in IZI Dashboard.

## Features Implemented

### 1. Background Color Customization
**Config Name:** `scorecardBgColor`
**Available Colors:**
- `default` - White background (default)
- `primary` - Blue gradient
- `success` - Green gradient
- `danger` - Red gradient
- `warning` - Orange/Yellow gradient
- `info` - Cyan gradient
- `dark` - Dark gray gradient

**Effect:** Changes the entire scorecard background with color gradient and automatically adjusts text colors for optimal contrast.

### 2. Icon Type Selection (Font Awesome 4.7.0)
**Config Name:** `scorecardIconType`
**Available Icons:** 30+ pre-configured Font Awesome icons + 600+ available icons

**Effect:** Displays an icon in the right side of the scorecard within a circular background.

### 3. Icon Color Customization
**Config Name:** `scorecardIconColor`
**Available Colors:**
- `primary` - Blue
- `success` - Green
- `danger` - Red
- `warning` - Orange/Yellow
- `info` - Cyan

**Effect:** Changes the icon color and its background highlight. When scorecard has a dark background, icon automatically adapts to white for visibility.

## Files Modified

### 1. Data Configuration
**File:** `data/izi_visual_config.xml`
- Added 3 new visual config records

**File:** `data/izi_visual_config_value.xml`
- Added 30+ Font Awesome icon options
- Added 7 background color options
- Added 5 icon color options

### 2. Frontend Rendering
**File:** `static/src/js/component/chart/amcharts_component.js`
- Updated `makeScorecardBasic()` function with Font Awesome support
- Added dynamic icon HTML generation using Font Awesome icons
- Supports both 'fa-iconname' and 'iconname' formats

### 3. Styling
**File:** `static/src/css/component/general/izi_chart.css`
- Added 40+ new CSS classes
- Updated icon sizing for Font Awesome (32px)
- Added gradient backgrounds for all color themes

### 4. Bug Fixes
**File:** `static/src/js/component/general/izi_autocomplete.js`
- Fixed Select2 initSelection error when editing analysis
- Added proper initSelection callback for query mode

## How to Use

### For End Users
1. Create or edit a dashboard
2. Add a scorecard analysis block
3. Right-click the scorecard → "Edit"
4. In the configuration panel, find:
   - **Background Color** - Select from 7 color options
   - **Icon Type** - Select from 30+ Font Awesome icons or "None"
   - **Icon Color** - Select from 5 color options
5. Changes apply immediately
6. Save the dashboard

### For Custom Icons
1. Visit http://fontawesome.io/icons/
2. Search for desired icon
3. Copy icon name (e.g., fa-lightbulb-o)
4. Paste into scorecard Icon Type field
5. Changes apply instantly

## Visual Design Details

### Color Palette
- **Primary (Blue):** #007BFF → #0056b3 (gradient)
- **Success (Green):** #28a745 → #1e7e34 (gradient)
- **Danger (Red):** #dc3545 → #ab2c35 (gradient)
- **Warning (Orange):** #ffc107 → #e0a800 (gradient)
- **Info (Cyan):** #17a2b8 → #0f7281 (gradient)
- **Dark (Gray):** #343a40 → #1f2124 (gradient)

### Icon Styling
- **Size:** 32px Font Awesome Icons
- **Container:** 60x60px circular container
- **Background:** Adaptive (20-30% opacity white on light, semi-transparent on colored backgrounds)
- **Positioning:** Aligned to the right side of scorecard

### Text Contrast
- **On white background:** Dark text (#333)
- **On colored backgrounds:** White text (#FFF)
- **On warning background:** Dark text (for yellow brightness)

## Testing Checklist

- [ ] Module installed successfully
- [ ] Configuration options appear in scorecard settings
- [ ] Background color changes apply to scorecard
- [ ] Text colors adjust appropriately for each background
- [ ] Icons display correctly in circular containers
- [ ] Icon colors match selection
- [ ] Icons adapt contrast on colored backgrounds
- [ ] Dashboard saves customizations
- [ ] Customizations persist after page reload
- [ ] Analysis editing works without errors

## Example Configurations

### Example 1: Sales KPI Card
- Background: Primary (Blue)
- Icon: fa-shopping-cart
- Icon Color: Primary
- Result: Professional blue card with shopping cart icon

### Example 2: Success Metric
- Background: Success (Green)
- Icon: fa-arrow-up
- Icon Color: Success
- Result: Green success card with upward trend indicator

### Example 3: Warning Alert
- Background: Warning (Orange)
- Icon: fa-warning
- Icon Color: Warning
- Result: Orange alert card with warning icon

## Browser Compatibility

- Chrome/Edge: ✓ Full support
- Firefox: ✓ Full support
- Safari: ✓ Full support
- IE 11: ✗ Font Awesome not supported

## Notes

- Configuration values are stored in `izi.analysis.visual.config` records
- CSS uses CSS3 gradients and flexbox (IE 10+)
- Font Awesome 4.7.0 is already loaded by Odoo framework
- Changes are applied dynamically without page reload
- No additional dependencies required
- Select2 initialization bug fixed for smooth analysis editing
