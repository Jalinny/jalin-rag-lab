# Frontend Changes

## Code Quality Tooling Setup

### New Files

#### `.prettierrc`
Prettier configuration with project-wide formatting rules:
- Double quotes, semicolons enabled
- 100-character print width
- 2-space indentation
- `es5` trailing commas

#### `.prettierignore`
Excludes `dist/` and `node_modules/` from Prettier formatting.

#### `eslint.config.js`
ESLint 9 flat config for TypeScript + React:
- `@eslint/js` recommended rules
- `typescript-eslint` strict type-aware rules
- `eslint-plugin-react-hooks` — enforces Rules of Hooks
- `eslint-plugin-react-refresh` — guards against HMR edge cases
- `dist/` excluded from linting

### Modified Files

#### `package.json`
Added new devDependencies:
- `@eslint/js` ^9.0.0
- `eslint` ^9.0.0
- `eslint-plugin-react-hooks` ^5.0.0
- `eslint-plugin-react-refresh` ^0.4.0
- `globals` ^15.0.0
- `prettier` ^3.0.0
- `typescript-eslint` ^8.0.0

Added new scripts:
| Script | Command | Purpose |
|--------|---------|---------|
| `lint` | `eslint .` | Run ESLint across all source files |
| `lint:fix` | `eslint . --fix` | Auto-fix ESLint violations |
| `format` | `prettier --write src` | Format all files in `src/` |
| `format:check` | `prettier --check src` | Check formatting without writing |
| `check` | `format:check && lint` | Full quality gate (CI-ready) |

#### `src/App.tsx`
Reformatted by Prettier for consistency:
- Multi-line JSX for elements exceeding 100-char print width
- Inline event handlers expanded to block form
- Ternary expressions wrapped in parentheses inside `.map()`
- Long type annotations broken across lines

No logic changes were made.

---

## Light / Dark Theme Toggle

### Modified Files

#### `src/App.tsx`

Added a light/dark theme toggle button to the header.

**State & effect:**
- New `darkMode` state initialized from `localStorage` (`rl_theme` key)
- `useEffect` applies/removes the `dark` class on `document.body` and persists the preference to `localStorage` on every toggle

**CSS — dark mode variables (`body.dark`):**
| Variable    | Light value | Dark value |
|-------------|-------------|------------|
| `--bg`      | `#e8d5b5`   | `#141414`  |
| `--surface` | `#f5ece0`   | `#1c1c1c`  |
| `--border`  | `#1a1a1a`   | `#383838`  |
| `--text`    | `#1a1a1a`   | `#e0d0bc`  |
| `--muted`   | `#6b5f50`   | `#7a6e60`  |
| `--yellow`  | `#f0e040`   | `#f0e040`  |
| `--black`   | `#111111`   | `#0d0d0d`  |
| `--white`   | `#faf5ee`   | `#2a2520`  |

**CSS — `.btn-theme`:**
- Small bordered icon button matching the existing `.btn-logout` style
- Displays `☽` in light mode, `☀` in dark mode
- Hover transitions color and border to full `--text` / `--border`

**Header JSX:**
- `<button class="btn-theme">` inserted between the status indicator and the sign-out button
- `title` attribute updates to reflect current mode for accessibility
