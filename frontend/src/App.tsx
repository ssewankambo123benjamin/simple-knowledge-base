import { useState, useCallback, useEffect } from 'react';
import {
  AppLayout,
  Alert,
  Box,
  ContentLayout,
  Flashbar,
  Header,
  SpaceBetween,
  StatusIndicator,
} from '@cloudscape-design/components';
import type { FlashbarProps } from '@cloudscape-design/components';

import { SearchInterface } from './components/SearchInterface';
import { SearchResults } from './components/SearchResults';
import { queryKnowledgeBase, checkHealth } from './api/client';
import type { SearchResult } from './api/types';

function App() {
  const [results, setResults] = useState<SearchResult[]>([]);
  const [currentQuery, setCurrentQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isHealthy, setIsHealthy] = useState<boolean | null>(null);
  const [notifications, setNotifications] = useState<FlashbarProps.MessageDefinition[]>([]);

  // Check backend health on mount
  useEffect(() => {
    checkHealth()
      .then(() => setIsHealthy(true))
      .catch(() => setIsHealthy(false));
  }, []);

  const addNotification = useCallback((
    type: 'success' | 'error' | 'warning' | 'info',
    header: string,
    content?: string
  ) => {
    const id = Date.now().toString();
    setNotifications((prev) => [
      ...prev,
      {
        type,
        header,
        content,
        dismissible: true,
        dismissLabel: 'Dismiss',
        onDismiss: () => {
          setNotifications((prev) => prev.filter((n) => n.id !== id));
        },
        id,
      },
    ]);
  }, []);

  const handleSearch = useCallback(async (query: string) => {
    setIsLoading(true);
    setCurrentQuery(query);
    setResults([]);

    try {
      const response = await queryKnowledgeBase({ query, top_k: 5 });
      setResults(response.results);
      
      if (response.results.length === 0) {
        addNotification('info', 'No results found', 'Try a different query');
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown error';
      addNotification('error', 'Search failed', message);
    } finally {
      setIsLoading(false);
    }
  }, [addNotification]);

  return (
    <AppLayout
      notifications={<Flashbar items={notifications} />}
      navigationHide
      toolsHide
      content={
        <ContentLayout
          header={
            <Header
              variant="h1"
              description="Semantic search powered by LanceDB and ML embeddings"
              info={
                isHealthy === null ? (
                  <StatusIndicator type="loading">Checking backend...</StatusIndicator>
                ) : isHealthy ? (
                  <StatusIndicator type="success">Backend connected</StatusIndicator>
                ) : (
                  <StatusIndicator type="error">Backend offline</StatusIndicator>
                )
              }
            >
              Knowledge Base
            </Header>
          }
        >
          <SpaceBetween size="l">
            {isHealthy === false && (
              <Alert type="error" header="Backend Unavailable">
                Unable to connect to the backend API. Please ensure the server is running at{' '}
                <Box variant="code">http://localhost:8000</Box>
              </Alert>
            )}
            
            <SearchInterface
              onSearch={handleSearch}
              isLoading={isLoading}
            />
            
            <SearchResults
              results={results}
              query={currentQuery}
              isLoading={isLoading}
            />
          </SpaceBetween>
        </ContentLayout>
      }
    />
  );
}

export default App;
