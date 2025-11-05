/**
 * Catalog Filtering Utilities
 *
 * Pure functions for filtering catalog items by content pack and search query.
 */

/**
 * Filter items by selected content packs
 * If selectedPacks is empty or contains 'all', return all items
 */
export function filterByContentPacks<T extends { content_pack?: string }>(
  items: T[],
  selectedPacks: string[]
): T[] {
  // If no packs selected or "all" selected, return all items
  if (selectedPacks.length === 0 || selectedPacks.includes('all')) {
    return items;
  }

  // Filter items that match selected content packs
  return items.filter(item => {
    // If item doesn't have content_pack field, include it (core content)
    if (!item.content_pack) {
      return selectedPacks.includes('core') || selectedPacks.includes('all');
    }
    return selectedPacks.includes(item.content_pack);
  });
}

/**
 * Filter items by search query across specified fields
 * Case-insensitive search
 */
export function filterBySearch<T>(
  items: T[],
  searchQuery: string,
  searchFields: (keyof T)[]
): T[] {
  if (!searchQuery || searchQuery.trim() === '') {
    return items;
  }

  const query = searchQuery.toLowerCase().trim();

  return items.filter(item => {
    return searchFields.some(field => {
      const value = item[field];
      if (typeof value === 'string') {
        return value.toLowerCase().includes(query);
      }
      if (typeof value === 'number') {
        return value.toString().includes(query);
      }
      return false;
    });
  });
}

/**
 * Combine multiple filter functions
 */
export function combineFilters<T>(
  items: T[],
  filters: Array<(items: T[]) => T[]>
): T[] {
  return filters.reduce((filtered, filterFn) => filterFn(filtered), items);
}

/**
 * Apply both content pack and search filtering
 */
export function applyAllFilters<T extends { content_pack?: string }>(
  items: T[],
  selectedPacks: string[],
  searchQuery: string,
  searchFields: (keyof T)[]
): T[] {
  return combineFilters(items, [
    (items) => filterByContentPacks(items, selectedPacks),
    (items) => filterBySearch(items, searchQuery, searchFields),
  ]);
}
