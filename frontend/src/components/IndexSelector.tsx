/**
 * IndexSelector Component
 * Reusable component for selecting an index from available indexes
 * Uses enhanced Select with filtering, icons, and tags
 */

import { useState, useEffect, useCallback } from 'react';
import {
  FormField,
  Select,
  SpaceBetween,
  StatusIndicator,
  Box,
} from '@cloudscape-design/components';
import type { SelectProps } from '@cloudscape-design/components';

import { listIndexes, getIndexRecordCount } from '../api/client';

interface IndexSelectorProps {
  selectedIndex: string | null;
  onIndexChange: (indexName: string | null) => void;
  disabled?: boolean;
  label?: string;
  description?: string;
  refreshTrigger?: number; // Increment to trigger refresh
}

// Use SelectProps.Option for proper typing
type IndexOption = SelectProps.Option;

export function IndexSelector({
  selectedIndex,
  onIndexChange,
  disabled = false,
  label = 'Index',
  description = 'Select an index to work with',
  refreshTrigger = 0,
}: IndexSelectorProps) {
  const [options, setOptions] = useState<IndexOption[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [recordCounts, setRecordCounts] = useState<Record<string, number>>({});

  const loadIndexes = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await listIndexes();
      
      // Fetch record counts for each index
      const counts: Record<string, number> = {};
      await Promise.all(
        response.indexes.map(async (indexName) => {
          try {
            const countResponse = await getIndexRecordCount(indexName);
            counts[indexName] = countResponse.record_count;
          } catch {
            counts[indexName] = -1; // Error fetching count
          }
        })
      );
      setRecordCounts(counts);

      const indexOptions: IndexOption[] = response.indexes.map((indexName) => ({
        label: indexName,
        value: indexName,
        description: counts[indexName] >= 0 
          ? `${counts[indexName].toLocaleString()} records` 
          : 'Unable to fetch count',
        iconName: 'folder' as const,
      }));

      setOptions(indexOptions);

      // If selected index no longer exists, clear selection
      if (selectedIndex && !response.indexes.includes(selectedIndex)) {
        onIndexChange(null);
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load indexes';
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }, [selectedIndex, onIndexChange]);

  useEffect(() => {
    loadIndexes();
  }, [loadIndexes, refreshTrigger]);

  const handleChange: SelectProps['onChange'] = ({ detail }) => {
    onIndexChange(detail.selectedOption?.value ?? null);
  };

  const selectedOption = selectedIndex
    ? options.find((opt) => opt.value === selectedIndex) ?? { label: selectedIndex, value: selectedIndex }
    : null;

  return (
    <FormField
      label={label}
      description={description}
      errorText={error}
    >
      <SpaceBetween size="xs">
        <Select
          selectedOption={selectedOption}
          onChange={handleChange}
          options={options}
          placeholder="Select an index"
          disabled={disabled || isLoading}
          loadingText="Loading indexes..."
          statusType={isLoading ? 'loading' : error ? 'error' : 'finished'}
          empty={
            <Box textAlign="center" color="text-body-secondary">
              No indexes found. Create one first.
            </Box>
          }
          filteringType="auto"
          filteringPlaceholder="Find an index"
          filteringAriaLabel="Filter indexes"
          selectedAriaLabel="Selected"
          triggerVariant="option"
          expandToViewport
        />
        {selectedIndex && recordCounts[selectedIndex] !== undefined && (
          <StatusIndicator type="info">
            {recordCounts[selectedIndex].toLocaleString()} records in index
          </StatusIndicator>
        )}
      </SpaceBetween>
    </FormField>
  );
}
