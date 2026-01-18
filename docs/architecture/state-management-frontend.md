# State Management - Frontend

## Overview
The frontend uses **Zustand** for state management with multiple specialized stores.

## Store Architecture

### `contextStore.ts`
Manages context/GDD element selections.

**State:**
- `selections`: Current context selection (characters, locations, items, etc.)
- `selectedRegion`: Currently selected region
- `selectedSubLocations`: Selected sub-locations
- Element lists: `characters`, `locations`, `items`, `species`, `communities`

**Actions:**
- `setSelections()`: Set full selection state
- `setElementLists()`: Load available elements from API
- `toggleCharacter/Location/Item/Species/Community()`: Toggle element selection
- `setElementMode()`: Set element mode (full/excerpt)
- `getElementMode()`: Get element mode
- `isElementSelected()`: Check if element is selected
- `setRegion()`: Set selected region
- `toggleSubLocation()`: Toggle sub-location
- `applyLinkedElements()`: Apply linked elements
- `clearSelections()`: Clear all selections
- `restoreState()`: Restore saved state

### `generationStore.ts`
Manages dialogue generation state.

**State:**
- Generation parameters
- Generated variants
- Current generation status

**Actions:**
- Generation control (start, cancel, etc.)
- Variant management

### `graphStore.ts`
Manages graph editor state.

**State:**
- Graph nodes and edges
- Current selection
- Layout information

**Actions:**
- Graph manipulation
- Node/edge operations
- Layout calculations

### `authStore.ts`
Manages authentication state.

**State:**
- Current user
- Authentication status
- Token information

**Actions:**
- Login/logout
- Token refresh
- User info updates

### `flagsStore.ts`
Manages game mechanics flags.

**State:**
- Available flags
- Selected flags
- Flag combinations

**Actions:**
- Flag selection
- Validation
- Combination management

### `vocabularyStore.ts`
Manages vocabulary entries.

**State:**
- Vocabulary list
- Selected terms

**Actions:**
- Load vocabulary
- Search terms

### `narrativeGuidesStore.ts`
Manages narrative guides.

**State:**
- Available guides
- Selected guide

**Actions:**
- Load guides
- Guide selection

### `contextConfigStore.ts`
Manages context configuration.

**State:**
- Field definitions
- Configuration settings

**Actions:**
- Load config
- Update settings

### `generationActionsStore.ts`
Manages generation action history.

**State:**
- Action history
- Undo/redo stack

**Actions:**
- Record actions
- Undo/redo

### `syncStore.ts`
Manages synchronization state.

**State:**
- Sync status
- Pending changes

**Actions:**
- Sync operations
- Conflict resolution

### `commandPaletteStore.ts`
Manages command palette state.

**State:**
- Available commands
- Command history

**Actions:**
- Command execution
- History management

## Data Flow

1. **User Action** → Component
2. **Component** → Store action
3. **Store** → API call (via React Query or direct)
4. **API Response** → Store update
5. **Store Update** → Component re-render

## Integration with React Query

Some stores integrate with React Query (`@tanstack/react-query`) for:
- Automatic caching
- Background refetching
- Optimistic updates
- Error handling

## State Persistence

- **LocalStorage**: Auth tokens, user preferences
- **Session Storage**: Temporary UI state
- **URL State**: Some filters/selections in query params
