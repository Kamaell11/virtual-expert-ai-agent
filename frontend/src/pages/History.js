import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Container,
  Paper,
  Button,
  CircularProgress,
  Alert,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
  TextField,
  InputAdornment,
} from '@mui/material';
import {
  Delete,
  Chat,
  SmartToy,
  Person,
  Search,
  Clear,
  Refresh,
} from '@mui/icons-material';
import { format } from 'date-fns';
import { queryAPI } from '../services/api';
import toast from 'react-hot-toast';

const History = () => {
  const [queries, setQueries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedQuery, setSelectedQuery] = useState(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [queryToDelete, setQueryToDelete] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    fetchQueries();
  }, []);

  const fetchQueries = async () => {
    try {
      setLoading(true);
      setError('');
      const response = await queryAPI.getQueries();
      console.log('API Response:', response); // Debug log
      
      // Handle API response format
      const data = response.queries || response || [];
      setQueries(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Failed to fetch queries:', error);
      setError('Failed to load chat history');
      setQueries([]);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteQuery = async (queryId) => {
    try {
      await queryAPI.deleteQuery(queryId);
      setQueries(queries.filter(q => q.id !== queryId));
      toast.success('Conversation deleted successfully');
      setDeleteDialogOpen(false);
      setQueryToDelete(null);
    } catch (error) {
      console.error('Failed to delete query:', error);
      toast.error('Failed to delete conversation');
    }
  };

  const openDeleteDialog = (query) => {
    setQueryToDelete(query);
    setDeleteDialogOpen(true);
  };

  const closeDeleteDialog = () => {
    setDeleteDialogOpen(false);
    setQueryToDelete(null);
  };

  const filteredQueries = queries.filter(query =>
    query.query_text?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    query.response_text?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom>
          Chat History
        </Typography>
        <Typography variant="body1" color="textSecondary" gutterBottom>
          Review your previous conversations with the AI assistant.
        </Typography>

        {/* Search and Actions */}
        <Box sx={{ display: 'flex', gap: 2, mt: 3, mb: 2 }}>
          <TextField
            placeholder="Search conversations..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            size="small"
            sx={{ flexGrow: 1 }}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <Search />
                </InputAdornment>
              ),
              endAdornment: searchTerm && (
                <InputAdornment position="end">
                  <IconButton
                    onClick={() => setSearchTerm('')}
                    edge="end"
                    size="small"
                  >
                    <Clear />
                  </IconButton>
                </InputAdornment>
              ),
            }}
          />
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={fetchQueries}
          >
            Refresh
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      {filteredQueries.length === 0 && !loading ? (
        <Card>
          <CardContent>
            <Box
              sx={{
                textAlign: 'center',
                py: 8,
                color: 'text.secondary',
              }}
            >
              <Chat sx={{ fontSize: 64, mb: 2, opacity: 0.5 }} />
              <Typography variant="h6" gutterBottom>
                {searchTerm ? 'No matching conversations found' : 'No chat history yet'}
              </Typography>
              <Typography variant="body2" sx={{ mb: 3 }}>
                {searchTerm ? 'Try adjusting your search terms' : 'Start a conversation to see your history here.'}
              </Typography>
              {!searchTerm && (
                <Button variant="contained" href="/chat">
                  Start First Chat
                </Button>
              )}
            </Box>
          </CardContent>
        </Card>
      ) : (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          {filteredQueries.map((query) => (
            <Card key={query.id} elevation={1}>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                  <Box sx={{ flex: 1 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                      <Person sx={{ fontSize: 18, mr: 1, color: 'primary.main' }} />
                      <Chip
                        label="You"
                        size="small"
                        variant="outlined"
                        color="primary"
                      />
                      <Typography variant="caption" color="textSecondary" sx={{ ml: 2 }}>
                        {format(new Date(query.timestamp), 'MMM dd, yyyy HH:mm')}
                      </Typography>
                    </Box>
                    <Typography variant="body1" sx={{ mb: 2, fontWeight: 500 }}>
                      {query.query_text}
                    </Typography>

                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                      <SmartToy sx={{ fontSize: 18, mr: 1, color: 'success.main' }} />
                      <Chip
                        label="AI Assistant"
                        size="small"
                        variant="outlined"
                        color="success"
                      />
                    </Box>
                    <Paper
                      elevation={0}
                      sx={{
                        p: 2,
                        backgroundColor: 'grey.50',
                        borderRadius: 2,
                      }}
                    >
                      <Typography
                        variant="body2"
                        sx={{
                          whiteSpace: 'pre-wrap',
                          maxHeight: selectedQuery?.id === query.id ? 'none' : '100px',
                          overflow: 'hidden',
                          position: 'relative',
                        }}
                      >
                        {query.response_text}
                      </Typography>
                      {query.response_text.length > 200 && selectedQuery?.id !== query.id && (
                        <Button
                          size="small"
                          onClick={() => setSelectedQuery(query)}
                          sx={{ mt: 1 }}
                        >
                          Read More
                        </Button>
                      )}
                      {selectedQuery?.id === query.id && (
                        <Button
                          size="small"
                          onClick={() => setSelectedQuery(null)}
                          sx={{ mt: 1 }}
                        >
                          Show Less
                        </Button>
                      )}
                    </Paper>
                  </Box>

                  <IconButton
                    onClick={() => openDeleteDialog(query)}
                    color="error"
                    size="small"
                    sx={{ ml: 2 }}
                  >
                    <Delete />
                  </IconButton>
                </Box>
              </CardContent>
            </Card>
          ))}
        </Box>
      )}

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteDialogOpen}
        onClose={closeDeleteDialog}
        aria-labelledby="delete-dialog-title"
      >
        <DialogTitle id="delete-dialog-title">
          Delete Conversation
        </DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete this conversation? This action cannot be undone.
          </Typography>
          {queryToDelete && (
            <Paper
              elevation={0}
              sx={{
                p: 2,
                mt: 2,
                backgroundColor: 'grey.50',
                borderRadius: 1,
              }}
            >
              <Typography variant="body2" color="textSecondary">
                "{queryToDelete.query_text}"
              </Typography>
            </Paper>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={closeDeleteDialog}>
            Cancel
          </Button>
          <Button
            onClick={() => handleDeleteQuery(queryToDelete.id)}
            color="error"
            variant="contained"
          >
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default History;