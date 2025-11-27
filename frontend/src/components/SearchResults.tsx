/**
 * Search Results Component
 * Displays the search results from the knowledge base
 */

import {
  Badge,
  Box,
  ColumnLayout,
  Container,
  ExpandableSection,
  Header,
  Icon,
  ProgressBar,
  SpaceBetween,
  StatusIndicator,
} from '@cloudscape-design/components';
import type { SearchResult } from '../api/types';

interface SearchResultsProps {
  results: SearchResult[];
  query: string;
  isLoading: boolean;
}

function formatScore(score: number): number {
  return Math.round(score * 100);
}

function extractFilename(path: string): string {
  return path.split('/').pop() || path;
}

interface ResultItemProps {
  item: SearchResult;
  rank: number;
}

function ResultItem({ item, rank }: ResultItemProps) {
  const score = formatScore(item.relevance_score);
  const filename = extractFilename(item.source_document);
  
  return (
    <Container
      header={
        <Header
          variant="h3"
          description={
            <SpaceBetween size="xs" direction="horizontal" alignItems="center">
              <Icon name="file" />
              <Box color="text-body-secondary" fontSize="body-s">
                {item.source_document}
              </Box>
            </SpaceBetween>
          }
          actions={
            <Badge color={score >= 80 ? 'green' : score >= 60 ? 'blue' : 'grey'}>
              {score}% match
            </Badge>
          }
        >
          <SpaceBetween size="xs" direction="horizontal" alignItems="center">
            <Box color="text-status-inactive" fontSize="body-s">#{rank}</Box>
            <Box>{filename}</Box>
          </SpaceBetween>
        </Header>
      }
    >
      <SpaceBetween size="m">
        {/* Relevance bar */}
        <ProgressBar
          value={score}
          variant="standalone"
          additionalInfo={`Relevance score: ${item.relevance_score.toFixed(3)}`}
        />
        
        {/* Content preview */}
        <ExpandableSection
          variant="footer"
          headerText="Content preview"
          defaultExpanded={rank === 1}
        >
          <Box
            padding="s"
            color="text-body-secondary"
            fontSize="body-s"
          >
            <pre style={{
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-word',
              fontFamily: 'Monaco, Consolas, "Courier New", monospace',
              fontSize: '13px',
              lineHeight: '1.5',
              margin: 0,
              backgroundColor: 'var(--color-background-code-editor-default)',
              padding: '12px',
              borderRadius: '4px',
              maxHeight: '300px',
              overflow: 'auto',
            }}>
              {item.content}
            </pre>
          </Box>
        </ExpandableSection>

        {/* Metadata */}
        <ColumnLayout columns={2} variant="text-grid">
          <div>
            <Box variant="awsui-key-label">Chunk offset</Box>
            <Box>{item.chunk_offset.toLocaleString()} characters</Box>
          </div>
          <div>
            <Box variant="awsui-key-label">Content length</Box>
            <Box>{item.content.length.toLocaleString()} characters</Box>
          </div>
        </ColumnLayout>
      </SpaceBetween>
    </Container>
  );
}

export function SearchResults({ results, query, isLoading }: SearchResultsProps) {
  if (isLoading) {
    return (
      <Container>
        <Box textAlign="center" padding="xxl">
          <SpaceBetween size="m" alignItems="center">
            <StatusIndicator type="loading">
              Searching for relevant content...
            </StatusIndicator>
            <Box color="text-body-secondary" fontSize="body-s">
              Embedding query and searching vector database
            </Box>
          </SpaceBetween>
        </Box>
      </Container>
    );
  }

  if (!query) {
    return (
      <Container>
        <Box textAlign="center" padding="xxl">
          <SpaceBetween size="m" alignItems="center">
            <Icon name="search" size="large" variant="subtle" />
            <Box color="text-body-secondary">
              Enter a query above to search the knowledge base
            </Box>
          </SpaceBetween>
        </Box>
      </Container>
    );
  }

  if (results.length === 0) {
    return (
      <Container>
        <Box textAlign="center" padding="xxl">
          <SpaceBetween size="m" alignItems="center">
            <StatusIndicator type="info">No results found</StatusIndicator>
            <Box color="text-body-secondary">
              Try rephrasing your query or using different keywords
            </Box>
          </SpaceBetween>
        </Box>
      </Container>
    );
  }

  return (
    <SpaceBetween size="l">
      <Header
        variant="h2"
        counter={`(${results.length})`}
        description={`Showing top results for: "${query}"`}
      >
        Search Results
      </Header>
      
      <SpaceBetween size="m">
        {results.map((item, index) => (
          <ResultItem
            key={`${item.source_document}-${item.chunk_offset}`}
            item={item}
            rank={index + 1}
          />
        ))}
      </SpaceBetween>
    </SpaceBetween>
  );
}
