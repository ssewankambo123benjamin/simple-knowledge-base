/**
 * AddKnowledge Component
 * Page for creating indexes and adding documents to the knowledge base
 */

import { useState, useCallback } from 'react';
import {
  Alert,
  Box,
  Button,
  ColumnLayout,
  Container,
  ExpandableSection,
  FileDropzone,
  FileTokenGroup,
  Form,
  FormField,
  Header,
  Input,
  SpaceBetween,
  Tiles,
  TokenGroup,
} from '@cloudscape-design/components';

import { IndexSelector } from './IndexSelector';
import { createIndex, encodeDocument, encodeBatch } from '../api/client';

// Index name validation pattern (must match backend)
const INDEX_NAME_PATTERN = /^[a-zA-Z][a-zA-Z0-9_-]*$/;

// Allowed file extensions for single document upload
const ALLOWED_EXTENSIONS = ['.md', '.txt'];

// Helper to validate file extension
function validateFileExtension(fileName: string): string | null {
  const extension = fileName.toLowerCase().substring(fileName.lastIndexOf('.'));
  if (!ALLOWED_EXTENSIONS.includes(extension)) {
    return `Unsupported file type "${extension}". Only ${ALLOWED_EXTENSIONS.join(', ')} files are allowed.`;
  }
  return null;
}

interface AddKnowledgeProps {
  onNotification: (
    type: 'success' | 'error' | 'warning' | 'info',
    header: string,
    content?: string
  ) => void;
}

export function AddKnowledge({ onNotification }: AddKnowledgeProps) {
  // Create Index state
  const [newIndexName, setNewIndexName] = useState('');
  const [isCreatingIndex, setIsCreatingIndex] = useState(false);
  const [indexRefreshTrigger, setIndexRefreshTrigger] = useState(0);

  // Document encoding state
  const [selectedIndex, setSelectedIndex] = useState<string | null>(null);
  const [documentPath, setDocumentPath] = useState('');
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [fileErrors, setFileErrors] = useState<Record<number, string>>({});
  const [isEncodingDoc, setIsEncodingDoc] = useState(false);

  // Batch encoding state
  const [directoryPath, setDirectoryPath] = useState('');
  const [filePatterns, setFilePatterns] = useState<string[]>(['*.md', '*.txt']);
  const [newPattern, setNewPattern] = useState('');
  const [isEncodingBatch, setIsEncodingBatch] = useState(false);

  // Mode selection
  const [encodeMode, setEncodeMode] = useState<'single' | 'batch'>('single');

  // Validate index name
  const isValidIndexName = INDEX_NAME_PATTERN.test(newIndexName);
  const indexNameError = newIndexName && !isValidIndexName
    ? 'Must start with a letter, followed by letters, numbers, underscores, or hyphens'
    : '';

  // Handle create index
  const handleCreateIndex = useCallback(async () => {
    if (!newIndexName || !isValidIndexName) return;

    setIsCreatingIndex(true);
    try {
      const response = await createIndex({ index_name: newIndexName });
      onNotification('success', 'Index created', response.message);
      setNewIndexName('');
      setIndexRefreshTrigger((prev) => prev + 1);
      // Auto-select the new index
      setSelectedIndex(newIndexName);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to create index';
      onNotification('error', 'Failed to create index', message);
    } finally {
      setIsCreatingIndex(false);
    }
  }, [newIndexName, isValidIndexName, onNotification]);

  // Handle single document encoding
  const handleEncodeDocument = useCallback(async () => {
    if (!selectedIndex || !documentPath) return;

    setIsEncodingDoc(true);
    try {
      const response = await encodeDocument({
        index_name: selectedIndex,
        document_path: documentPath,
      });
      onNotification(
        'success',
        'Document encoded',
        `${response.chunk_count} chunks created from ${response.document_path}`
      );
      setDocumentPath('');
      setIndexRefreshTrigger((prev) => prev + 1);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to encode document';
      onNotification('error', 'Encoding failed', message);
    } finally {
      setIsEncodingDoc(false);
    }
  }, [selectedIndex, documentPath, onNotification]);

  // Handle batch encoding
  const handleEncodeBatch = useCallback(async () => {
    if (!selectedIndex || !directoryPath) return;

    setIsEncodingBatch(true);
    try {
      const response = await encodeBatch({
        index_name: selectedIndex,
        directory_path: directoryPath,
        file_patterns: filePatterns.length > 0 ? filePatterns : undefined,
      });
      onNotification(
        'success',
        'Batch processing started',
        `${response.documents_queued} documents queued for processing`
      );
      setDirectoryPath('');
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to start batch encoding';
      onNotification('error', 'Batch encoding failed', message);
    } finally {
      setIsEncodingBatch(false);
    }
  }, [selectedIndex, directoryPath, filePatterns, onNotification]);

  // Handle adding a file pattern
  const handleAddPattern = () => {
    if (newPattern && !filePatterns.includes(newPattern)) {
      setFilePatterns([...filePatterns, newPattern]);
      setNewPattern('');
    }
  };

  return (
    <SpaceBetween size="l">
      {/* Help Section - How it works */}
      <ExpandableSection
        headerText="How it works"
        variant="container"
        defaultExpanded={false}
      >
        <ColumnLayout columns={3} variant="text-grid">
          <div>
            <Box variant="awsui-key-label">1. Create Index</Box>
            <Box color="text-body-secondary">
              An index is a container for your knowledge. Each index can hold
              documents related to a specific topic or project.
            </Box>
          </div>
          <div>
            <Box variant="awsui-key-label">2. Add Documents</Box>
            <Box color="text-body-secondary">
              Documents are automatically chunked, embedded, and stored in the
              vector database for semantic search.
            </Box>
          </div>
          <div>
            <Box variant="awsui-key-label">3. Search</Box>
            <Box color="text-body-secondary">
              Use natural language queries to find relevant content. Results
              are ranked by semantic similarity.
            </Box>
          </div>
        </ColumnLayout>
      </ExpandableSection>

      {/* Section 1: Create Index */}
      <Container
        header={
          <Header
            variant="h2"
            description="Create a new index to store your knowledge"
          >
            <SpaceBetween size="xs" direction="horizontal" alignItems="center">
              <img src="/add-index.svg" alt="" style={{ height: '24px', width: '24px' }} />
              <span>Create Index</span>
            </SpaceBetween>
          </Header>
        }
      >
        <Form
          actions={
            <Button
              variant="primary"
              onClick={handleCreateIndex}
              loading={isCreatingIndex}
              loadingText="Creating..."
              disabled={!newIndexName || !isValidIndexName}
              iconName="add-plus"
            >
              Create Index
            </Button>
          }
        >
          <FormField
            label="Index Name"
            description="A unique name for your index (letters, numbers, underscores, hyphens)"
            errorText={indexNameError}
            constraintText="Must start with a letter"
          >
            <Input
              value={newIndexName}
              onChange={({ detail }) => setNewIndexName(detail.value)}
              placeholder="my-knowledge-base"
              disabled={isCreatingIndex}
            />
          </FormField>
        </Form>
      </Container>

      {/* Section 2: Add Documents */}
      <Container
        header={
          <Header
            variant="h2"
            description="Add documents to an existing index"
          >
            <SpaceBetween size="xs" direction="horizontal" alignItems="center">
              <img src="/add-file.svg" alt="" style={{ height: '24px', width: '24px' }} />
              <span>Add Documents</span>
            </SpaceBetween>
          </Header>
        }
      >
        <SpaceBetween size="l">
          {/* Index Selection */}
          <IndexSelector
            selectedIndex={selectedIndex}
            onIndexChange={setSelectedIndex}
            refreshTrigger={indexRefreshTrigger}
            description="Select the index to add documents to"
          />

          {!selectedIndex && (
            <Alert type="info">
              Select an index above to add documents. If you don't have any indexes, create one first.
            </Alert>
          )}

          {selectedIndex && (
            <>
              {/* Mode Selection */}
              <FormField label="Document Source">
                <Tiles
                  value={encodeMode}
                  onChange={({ detail }) => setEncodeMode(detail.value as 'single' | 'batch')}
                  items={[
                    {
                      value: 'single',
                      label: 'Single Document',
                      description: 'Add one document by file path',
                    },
                    {
                      value: 'batch',
                      label: 'Batch Directory',
                      description: 'Process all matching documents in a directory',
                    },
                  ]}
                />
              </FormField>

              {/* Single Document Mode */}
              {encodeMode === 'single' && (
                <SpaceBetween size="m">
                  {/* File Dropzone for visual feedback */}
                  <FormField
                    label="Select Document"
                    description="Drag and drop a file to preview, then enter the server path below"
                  >
                    <FileDropzone
                      onChange={({ detail }) => {
                        const files = detail.value;
                        setSelectedFiles(files);
                        
                        // Validate each file and set errors
                        const errors: Record<number, string> = {};
                        files.forEach((file, index) => {
                          const error = validateFileExtension(file.name);
                          if (error) {
                            errors[index] = error;
                          }
                        });
                        setFileErrors(errors);
                        
                        // Use the file name as a hint for the path (only for valid files)
                        if (files.length > 0) {
                          const fileName = files[0].name;
                          const error = validateFileExtension(fileName);
                          if (!error && !documentPath) {
                            setDocumentPath(`/path/to/${fileName}`);
                          }
                        }
                      }}
                    >
                      <Box textAlign="center" padding="l" color="text-body-secondary">
                        <SpaceBetween size="s" alignItems="center">
                          <Box fontSize="heading-m">Drop file here</Box>
                          <Box>or click to browse</Box>
                          <Box fontSize="body-s">
                            Supported formats: {ALLOWED_EXTENSIONS.join(', ')}
                          </Box>
                        </SpaceBetween>
                      </Box>
                    </FileDropzone>
                  </FormField>

                  {/* Display selected files with validation errors */}
                  {selectedFiles.length > 0 && (
                    <FileTokenGroup
                      items={selectedFiles.map((file, index) => ({
                        file,
                        loading: isEncodingDoc,
                        errorText: fileErrors[index],
                      }))}
                      onDismiss={({ detail }) => {
                        setSelectedFiles((files) =>
                          files.filter((_, index) => index !== detail.fileIndex)
                        );
                        // Also remove the error for dismissed file
                        setFileErrors((prev) => {
                          const newErrors: Record<number, string> = {};
                          Object.keys(prev).forEach((key) => {
                            const keyNum = parseInt(key);
                            if (keyNum < detail.fileIndex) {
                              newErrors[keyNum] = prev[keyNum];
                            } else if (keyNum > detail.fileIndex) {
                              newErrors[keyNum - 1] = prev[keyNum];
                            }
                          });
                          return newErrors;
                        });
                      }}
                    />
                  )}

                  <Alert type="info" statusIconAriaLabel="Info">
                    <strong>Note:</strong> Enter the server-side file path below. The file must be accessible from the backend server.
                  </Alert>

                  <Form
                    actions={
                      <Button
                        variant="primary"
                        onClick={handleEncodeDocument}
                        loading={isEncodingDoc}
                        loadingText="Encoding..."
                        disabled={!documentPath}
                        iconName="upload"
                      >
                        Encode Document
                      </Button>
                    }
                  >
                    <FormField
                      label="Document Path"
                      description="Absolute path to the document file on the server"
                      constraintText={`Supported formats: ${ALLOWED_EXTENSIONS.join(', ')}`}
                    >
                      <Input
                        value={documentPath}
                        onChange={({ detail }) => setDocumentPath(detail.value)}
                        placeholder="/path/to/document.md"
                        disabled={isEncodingDoc}
                      />
                    </FormField>
                  </Form>
                </SpaceBetween>
              )}

              {/* Batch Mode */}
              {encodeMode === 'batch' && (
                <Form
                  actions={
                    <Button
                      variant="primary"
                      onClick={handleEncodeBatch}
                      loading={isEncodingBatch}
                      loadingText="Starting batch..."
                      disabled={!directoryPath}
                      iconName="folder"
                    >
                      Start Batch Processing
                    </Button>
                  }
                >
                  <SpaceBetween size="m">
                    <FormField
                      label="Directory Path"
                      description="Absolute path to the directory containing documents"
                    >
                      <Input
                        value={directoryPath}
                        onChange={({ detail }) => setDirectoryPath(detail.value)}
                        placeholder="/path/to/documents/"
                        disabled={isEncodingBatch}
                      />
                    </FormField>

                    <ExpandableSection
                      headerText="File Patterns"
                      variant="footer"
                      defaultExpanded={false}
                    >
                      <SpaceBetween size="s">
                        <Box color="text-body-secondary" fontSize="body-s">
                          Specify which file patterns to include. Defaults to common text formats.
                        </Box>
                        
                        <TokenGroup
                          items={filePatterns.map((pattern) => ({ label: pattern }))}
                          onDismiss={({ detail }) => {
                            setFilePatterns(
                              filePatterns.filter((_, i) => i !== detail.itemIndex)
                            );
                          }}
                        />

                        <SpaceBetween size="xs" direction="horizontal">
                          <Input
                            value={newPattern}
                            onChange={({ detail }) => setNewPattern(detail.value)}
                            placeholder="*.json"
                            onKeyDown={({ detail }) => {
                              if (detail.key === 'Enter') handleAddPattern();
                            }}
                          />
                          <Button
                            onClick={handleAddPattern}
                            disabled={!newPattern}
                            iconName="add-plus"
                          >
                            Add
                          </Button>
                        </SpaceBetween>
                      </SpaceBetween>
                    </ExpandableSection>

                    <Alert type="info" header="Background Processing">
                      Batch processing runs in the background. You can continue using the application
                      while documents are being processed.
                    </Alert>
                  </SpaceBetween>
                </Form>
              )}
            </>
          )}
        </SpaceBetween>
      </Container>
    </SpaceBetween>
  );
}
