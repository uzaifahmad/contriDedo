# contriDedo Design System

## Product character

contriDedo makes shared trip spending feel calm, transparent, and human. The visual language takes cues from a well-kept field journal: clear editorial hierarchy, warm paper surfaces, small travel-inspired details, and crisp financial information. Friendly, never childish. Useful at a glance, never a wall of cards.

## Brand

The wordmark is lowercase `contriDedo`, with `Dedo` highlighted in the citrus accent. Pair it with a compact rounded-square mark containing a lowercase `c`. Keep the brand name visible in the web navigation and Android app bar.

## Color tokens

- Forest: `#224A3E` (primary actions, navigation, strong headings)
- Deep forest: `#073328` (dark navigation and high-contrast surfaces)
- Citrus: `#D8F042` (small brand accents, selected states, positive emphasis)
- Paper: `#FAF7F2` (main canvas)
- White: `#FFFFFF` (forms and content surfaces)
- Ink: `#1D2E29` (primary text)
- Muted: `#707C75` (secondary text)
- Rule: `#E3DDD3` (dividers and subtle outlines)
- Clay: `#C86D51` (warm expense/category accent, never error state)
- Sky: `#4A829E` (secondary travel accent)
- Success: `#4C744A`; warning: `#A66E2D`; error: `#A94335`

Maintain WCAG AA contrast for text and interactive controls. Use forest on paper, white on forest, and ink on citrus. Never use color alone to communicate a balance state.

## Typography

- Display and page titles: `Newsreader`, regular, expressive but legible
- Interface and body: `DM Sans`, 400/500/600/700
- Amounts: `DM Sans` with tabular numerals
- Use compact page headings (32-40px desktop, 28-34px mobile), 14-16px body, 11-13px supporting labels. Avoid oversized marketing type outside the landing hero.

## Shape, spacing, and depth

- Base spacing unit: 4px; common rhythm: 8, 12, 16, 24, 32, 48px
- Buttons and fields: 4px radius; repeated data rows stay unframed
- Use 8px radius maximum for cards and dialogs
- Use thin rules, whitespace, and aligned columns before adding containers
- Shadows are reserved for overlays and floating controls, not dashboard sections

## Components and behavior

- Primary action: forest fill, white label, leading or trailing Lucide icon
- Secondary action: transparent or paper surface with a forest outline
- Inputs: persistent labels, visible keyboard focus ring, useful inline errors
- Split mode: segmented control for equal, percentage, exact
- Participant selection: checkbox rows with name, initials/avatar, and resulting share
- Amounts: decimal strings at API boundaries; display localized currency; allocate equal splits in integer cents and explain remainder-cent allocation
- Dashboard: trip switcher/navigation, trip summary, balances, and recent expense rows in a scan-first hierarchy
- Mobile navigation: bottom destinations for Trips, Activity, Balances, and Profile
- Dialogs and sheets must support keyboard use, close affordances, and reduced-motion preferences

## Imagery and tone

Use bright, real travel photography that shows a recognizable place or activity; avoid abstract gradient blobs and generic stock-team imagery. Keep images secondary to expense data on the dashboard. Copy is short, warm, and direct. Avoid guilt-oriented settlement language.

## Google Stitch source

Project: `6287107163682911343` (`contriDedo | Trip expense sharing`)

- Desktop landing: `d8263151ac574a838f212c0e8245092f`
- Desktop trip ledger: `e6396b9e3f85402088185103d762f70e`
- Android trip journal: `c90f19ab131a4258be86aa58c17fbbb7`
- Android add expense: `c9048cfbfe5a411b859daad26d1b13d3`
