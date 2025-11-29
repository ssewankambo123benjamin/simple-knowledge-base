import { useState, useCallback, useEffect } from 'react';
import {
  AppLayout,
  Alert,
  Box,
  ContentLayout,
  Flashbar,
  Header,
  Icon,
  SpaceBetween,
  StatusIndicator,
  Tabs,
} from '@cloudscape-design/components';
import type { FlashbarProps } from '@cloudscape-design/components';

import { SearchInterface } from './components/SearchInterface';
import { SearchResults } from './components/SearchResults';
import { AddKnowledge } from './components/AddKnowledge';
import { queryKnowledgeBase, checkHealth } from './api/client';
import type { SearchResult } from './api/types';

// Application logo
import logoSvg from '/idea-bulb-learning-knowledge-education-book-idea.svg';

function App() {
  const [activeTab, setActiveTab] = useState('search');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [currentQuery, setCurrentQuery] = useState('');
  const [currentIndex, setCurrentIndex] = useState('');
  const [searchTimeMs, setSearchTimeMs] = useState<number | null>(null);
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

  const handleSearch = useCallback(async (query: string, indexName: string) => {
    setIsLoading(true);
    setCurrentQuery(query);
    setCurrentIndex(indexName);
    setResults([]);
    setSearchTimeMs(null);

    const startTime = performance.now();

    try {
      const response = await queryKnowledgeBase({ 
        query, 
        index_name: indexName,
        top_k: 5 
      });
      
      const endTime = performance.now();
      setSearchTimeMs(Math.round(endTime - startTime));
      setResults(response.results);
      
      if (response.results.length === 0) {
        addNotification('info', 'No results found', 'Try a different query');
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown error';
      addNotification('error', 'Search failed', message);
      setSearchTimeMs(null);
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
              <SpaceBetween size="xs" direction="horizontal" alignItems="center">
                <img src={logoSvg} alt="Logo" style={{ height: '32px', width: '32px' }} />
                <span>Simple Knowledge Base</span>
              </SpaceBetween>
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

            <Tabs
              activeTabId={activeTab}
              onChange={({ detail }) => setActiveTab(detail.activeTabId)}
              tabs={[
                {
                  id: 'search',
                  label: (
                    <SpaceBetween size="xs" direction="horizontal" alignItems="center">
                      <Icon name="search" />
                      <span>Search</span>
                    </SpaceBetween>
                  ),
                  content: (
                    <SpaceBetween size="l">
                      <SearchInterface
                        onSearch={handleSearch}
                        isLoading={isLoading}
                      />
                      <SearchResults
                        results={results}
                        query={currentQuery}
                        indexName={currentIndex}
                        searchTimeMs={searchTimeMs}
                        isLoading={isLoading}
                      />
                    </SpaceBetween>
                  ),
                },
                {
                  id: 'add-knowledge',
                  label: (
                    <SpaceBetween size="xs" direction="horizontal" alignItems="center">
                      <Icon name="upload" />
                      <span>Add Knowledge</span>
                    </SpaceBetween>
                  ),
                  content: (
                    <AddKnowledge onNotification={addNotification} />
                  ),
                },
              ]}
            />
          </SpaceBetween>
        </ContentLayout>
      }
    />
  );
}

export default App;
