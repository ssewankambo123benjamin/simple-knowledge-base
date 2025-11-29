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
  indexName: string;
  searchTimeMs: number | null;
  isLoading: boolean;
}

// LanceDB default similarity metric
const SIMILARITY_METRIC = 'L2 (Euclidean)';

function formatScore(score: number): number {
  return Math.round(score * 100);
}

function extractFilename(path: string): string {
  return path.split('/').pop() || path;
}

interface ResultItemProps {
  item: SearchResult;
  rank: number;
  totalResults: number;
  minScore: number;
  maxScore: number;
}

// Get badge color based on relative position in result set
function getBadgeColor(score: number, minScore: number, maxScore: number, totalResults: number): 'green' | 'red' | 'severity-medium' {
  // If only one result or all same scores, use green
  if (totalResults === 1 || maxScore === minScore) return 'green';
  
  // Calculate position in range (0 = worst, 1 = best)
  const range = maxScore - minScore;
  const position = (score - minScore) / range;
  
  // Top third = green, middle third = orange, bottom third = red
  if (position >= 0.67) return 'green';
  if (position >= 0.33) return 'severity-medium';
  return 'red';
}

function ResultItem({ item, rank, totalResults, minScore, maxScore }: ResultItemProps) {
  const score = formatScore(item.relevance_score);
  const filename = extractFilename(item.source_document);
  const badgeColor = getBadgeColor(item.relevance_score, minScore, maxScore, totalResults);
  
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
            <Badge color={badgeColor}>
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

export function SearchResults({ results, query, indexName, searchTimeMs, isLoading }: SearchResultsProps) {
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

  // Format search time as seconds with ms in brackets
  const formatSearchTime = (ms: number | null): string => {
    if (ms === null) return '—';
    const seconds = (ms / 1000).toFixed(3);
    return `${seconds}s (${ms}ms)`;
  };

  return (
    <SpaceBetween size="l">
      {/* Search Results Header - Compact layout */}
      <Container
        header={
          <Header
            variant="h2"
            description={<>Displaying top <strong>{results.length}</strong> results for: <strong>"{query}"</strong></>}
          >
            <SpaceBetween size="xs" direction="horizontal" alignItems="center">
              <Icon name="search" />
              <span>Search Results</span>
            </SpaceBetween>
          </Header>
        }
      >
        {/* Search metadata in a clean grid */}
        <ColumnLayout columns={3} variant="text-grid">
          <div>
            <Box variant="awsui-key-label">Index</Box>
            <SpaceBetween size="xs" direction="horizontal" alignItems="center">
              <Icon name="folder" variant="subtle" />
              <Box fontWeight="bold" color="text-status-warning">{indexName || 'Default'}</Box>
            </SpaceBetween>
          </div>
          <div>
            <Box variant="awsui-key-label">Similarity Metric</Box>
            <SpaceBetween size="xs" direction="horizontal" alignItems="center">
              <Icon name="status-info" variant="subtle" />
              <Box>{SIMILARITY_METRIC}</Box>
            </SpaceBetween>
          </div>
          <div>
            <Box variant="awsui-key-label">Search Time</Box>
            <SpaceBetween size="xs" direction="horizontal" alignItems="center">
              <Icon name="status-positive" variant="success" />
              <Box fontWeight="bold">{formatSearchTime(searchTimeMs)}</Box>
            </SpaceBetween>
          </div>
        </ColumnLayout>
      </Container>
      
      {/* Results list */}
      <SpaceBetween size="m">
        {(() => {
          // Calculate min/max scores for relative coloring
          const scores = results.map(r => r.relevance_score);
          const minScore = Math.min(...scores);
          const maxScore = Math.max(...scores);
          
          return results.map((item, index) => (
            <ResultItem
              key={`${item.source_document}-${item.chunk_offset}`}
              item={item}
              rank={index + 1}
              totalResults={results.length}
              minScore={minScore}
              maxScore={maxScore}
            />
          ));
        })()}
      </SpaceBetween>
    </SpaceBetween>
  );
}
