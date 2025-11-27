/**
 * Search Interface Component
 * Main search input with submit functionality
 */

import { useState } from 'react';
import {
  Button,
  Container,
  FormField,
  Header,
  Input,
  SpaceBetween,
} from '@cloudscape-design/components';

interface SearchInterfaceProps {
  onSearch: (query: string) => void;
  isLoading: boolean;
}

export function SearchInterface({ onSearch, isLoading }: SearchInterfaceProps) {
  const [query, setQuery] = useState('');

  const handleSubmit = () => {
    if (query.trim()) {
      onSearch(query.trim());
    }
  };

  const handleKeyDown = ({ detail }: { detail: { key: string } }) => {
    if (detail.key === 'Enter' && query.trim() && !isLoading) {
      handleSubmit();
    }
  };

  return (
    <Container
      header={
        <Header
          variant="h2"
          description="Search through your knowledge base using natural language queries"
        >
          Semantic Search
        </Header>
      }
    >
      <SpaceBetween size="m">
        <FormField
          label="Search Query"
          description="Enter your question or search terms"
        >
          <Input
            value={query}
            onChange={({ detail }) => setQuery(detail.value)}
            onKeyDown={handleKeyDown}
            placeholder="e.g., How do I create a table in LanceDB?"
            disabled={isLoading}
          />
        </FormField>
        <Button
          variant="primary"
          onClick={handleSubmit}
          loading={isLoading}
          loadingText="Searching..."
          disabled={!query.trim()}
          iconName="search"
        >
          Search
        </Button>
      </SpaceBetween>
    </Container>
  );
}
