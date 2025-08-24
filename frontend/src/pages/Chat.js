import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  TextField,
  Button,
  Typography,
  Container,
  Paper,
  CircularProgress,
  Alert,
  Chip,
} from '@mui/material';
import { Send, SmartToy, Person, AttachFile, GetApp, Upload } from '@mui/icons-material';
import { queryAPI } from '../services/api';
import { format } from 'date-fns';
import toast from 'react-hot-toast';

const Chat = () => {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!inputValue.trim() || loading) return;

    const userMessage = {
      id: Date.now(),
      text: inputValue.trim(),
      isUser: true,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue('');
    setLoading(true);
    setError('');

    try {
      const response = await queryAPI.createQuery({
        query_text: userMessage.text,
        context: null,
      });

      const botMessage = {
        id: Date.now() + 1,
        text: response.response_text,
        isUser: false,
        timestamp: new Date(response.timestamp),
      };

      setMessages((prev) => [...prev, botMessage]);

      // Check if AI wants to generate a file
      if (response.file_action && response.file_action.action === 'generate_csv') {
        try {
          const token = localStorage.getItem('accessToken');
          const fileResponse = await fetch('/api/files/generate-csv', {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              description: response.file_action.description,
              filename: response.file_action.filename
            }),
          });

          if (fileResponse.ok) {
            const blob = await fileResponse.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = response.file_action.filename || 'generated_data.csv';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);

            const fileMessage = {
              id: Date.now() + 2,
              text: `📥 File "${response.file_action.filename}" has been downloaded successfully!`,
              isUser: false,
              timestamp: new Date(),
            };

            setMessages((prev) => [...prev, fileMessage]);
            toast.success('CSV file generated and downloaded!');
          }
        } catch (fileError) {
          console.error('Error generating file:', fileError);
          toast.error('Failed to generate file');
        }
      }
    } catch (error) {
      console.error('Failed to send message:', error);
      const errorMessage = error.response?.data?.detail || 'Failed to get response from AI';
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const clearChat = () => {
    setMessages([]);
    setError('');
  };

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    setSelectedFile(file);
  };

  const handleFileUpload = async () => {
    if (!selectedFile) {
      toast.error('Please select a file first');
      return;
    }

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const token = localStorage.getItem('accessToken');
      const response = await fetch('/api/files/analyze', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      });

      if (response.ok) {
        const result = await response.json();
        
        const userMessage = {
          id: Date.now(),
          text: `📎 Uploaded file: ${selectedFile.name}`,
          isUser: true,
          timestamp: new Date(),
          hasFile: true,
        };

        const aiMessage = {
          id: Date.now() + 1,
          text: `I've analyzed your file "${result.filename}":\n\n${JSON.stringify(result.analysis, null, 2)}`,
          isUser: false,
          timestamp: new Date(),
        };

        setMessages(prev => [...prev, userMessage, aiMessage]);
        setSelectedFile(null);
        fileInputRef.current.value = '';
        toast.success('File uploaded and analyzed successfully!');
      } else {
        toast.error('Failed to upload file');
      }
    } catch (error) {
      toast.error('Error uploading file');
      console.error('File upload error:', error);
    }
  };

  const handleExportChat = async () => {
    try {
      // Generate CSV content from chat messages
      const csvContent = [
        ['Timestamp', 'Sender', 'Message'],
        ...messages.map(msg => [
          format(msg.timestamp, 'yyyy-MM-dd HH:mm:ss'),
          msg.isUser ? 'User' : 'AI Assistant',
          msg.text.replace(/"/g, '""') // Escape quotes for CSV
        ])
      ].map(row => 
        row.map(field => `"${field}"`).join(',')
      ).join('\n');

      // Create and download the file
      const blob = new Blob([csvContent], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = `chat_export_${format(new Date(), 'yyyy-MM-dd_HH-mm')}.csv`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);

      toast.success('Chat exported to CSV!');
    } catch (error) {
      toast.error('Error exporting chat');
      console.error('Chat export error:', error);
    }
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>
        AI Chat Assistant
      </Typography>
      <Typography variant="body1" color="textSecondary" gutterBottom>
        Ask me anything! I'm here to help you with information, analysis, and problem-solving.
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      <Card sx={{ height: '75vh', display: 'flex', flexDirection: 'column' }}>
        <CardContent sx={{ flex: 1, display: 'flex', flexDirection: 'column', p: 0, overflow: 'hidden' }}>
          {/* Messages Area */}
          <Box
            sx={{
              flex: 1,
              overflowY: 'scroll',
              overflowX: 'hidden',
              p: 2,
              display: 'flex',
              flexDirection: 'column',
              gap: 2,
              maxHeight: '100%',
              '&::-webkit-scrollbar': {
                width: '12px',
              },
              '&::-webkit-scrollbar-track': {
                background: '#f1f1f1',
                borderRadius: '6px',
              },
              '&::-webkit-scrollbar-thumb': {
                background: '#888',
                borderRadius: '6px',
                '&:hover': {
                  background: '#555',
                },
              },
              /* Firefox scrollbar */
              scrollbarWidth: 'thin',
              scrollbarColor: '#888 #f1f1f1',
            }}
          >
            {messages.length === 0 && (
              <Box
                sx={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  height: '100%',
                  textAlign: 'center',
                  color: 'text.secondary',
                }}
              >
                <SmartToy sx={{ fontSize: 64, mb: 2, opacity: 0.5 }} />
                <Typography variant="h6" gutterBottom>
                  Start a conversation
                </Typography>
                <Typography variant="body2">
                  Type your question below and I'll help you find the answer.
                </Typography>
              </Box>
            )}

            {messages.map((message) => (
              <Box
                key={message.id}
                sx={{
                  display: 'flex',
                  justifyContent: message.isUser ? 'flex-end' : 'flex-start',
                  mb: 1,
                }}
              >
                <Paper
                  elevation={1}
                  sx={{
                    p: 2,
                    maxWidth: '70%',
                    backgroundColor: message.isUser
                      ? 'primary.main'
                      : 'grey.100',
                    color: message.isUser ? 'primary.contrastText' : 'text.primary',
                  }}
                >
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                    {message.isUser ? (
                      <Person sx={{ fontSize: 18, mr: 1 }} />
                    ) : (
                      <SmartToy sx={{ fontSize: 18, mr: 1 }} />
                    )}
                    <Chip
                      label={message.isUser ? 'You' : 'AI Assistant'}
                      size="small"
                      variant="outlined"
                      sx={{
                        color: message.isUser ? 'primary.contrastText' : 'primary.main',
                        borderColor: message.isUser ? 'primary.contrastText' : 'primary.main',
                      }}
                    />
                  </Box>
                  <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                    {message.text}
                  </Typography>
                  <Typography
                    variant="caption"
                    sx={{
                      display: 'block',
                      mt: 1,
                      opacity: 0.8,
                      textAlign: 'right',
                    }}
                  >
                    {format(message.timestamp, 'HH:mm')}
                  </Typography>
                </Paper>
              </Box>
            ))}

            {loading && (
              <Box sx={{ display: 'flex', justifyContent: 'flex-start', mb: 1 }}>
                <Paper
                  elevation={1}
                  sx={{
                    p: 2,
                    backgroundColor: 'grey.100',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 1,
                  }}
                >
                  <SmartToy sx={{ fontSize: 18 }} />
                  <CircularProgress size={16} />
                  <Typography variant="body2">AI is thinking...</Typography>
                </Paper>
              </Box>
            )}

            <div ref={messagesEndRef} />
          </Box>

          {/* Input Area */}
          <Box
            sx={{
              borderTop: 1,
              borderColor: 'divider',
              p: 2,
            }}
          >
            {/* File Upload Section */}
            <Box sx={{ mb: 2, display: 'flex', gap: 1, alignItems: 'center', flexWrap: 'wrap' }}>
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileSelect}
                style={{ display: 'none' }}
                accept=".csv,.txt,.json,.pdf,.doc,.docx"
              />
              <Button
                variant="outlined"
                size="small"
                startIcon={<AttachFile />}
                onClick={() => fileInputRef.current?.click()}
                disabled={loading}
              >
                Select File
              </Button>
              {selectedFile && (
                <>
                  <Chip
                    label={selectedFile.name}
                    size="small"
                    onDelete={() => setSelectedFile(null)}
                  />
                  <Button
                    variant="contained"
                    size="small"
                    startIcon={<Upload />}
                    onClick={handleFileUpload}
                    disabled={loading}
                  >
                    Upload & Analyze
                  </Button>
                </>
              )}
              <Button
                variant="outlined"
                size="small"
                startIcon={<GetApp />}
                onClick={handleExportChat}
                disabled={loading || messages.length === 0}
                sx={{ ml: 'auto' }}
              >
                Export Chat
              </Button>
            </Box>
            
            <Box
              component="form"
              onSubmit={handleSubmit}
              sx={{ display: 'flex', gap: 1 }}
            >
              <TextField
                fullWidth
                multiline
                maxRows={4}
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Type your message here... (Press Enter to send, Shift+Enter for new line)"
                disabled={loading}
                variant="outlined"
                size="small"
              />
              <Button
                type="submit"
                variant="contained"
                disabled={!inputValue.trim() || loading}
                sx={{ minWidth: 'auto', px: 2 }}
              >
                {loading ? <CircularProgress size={20} /> : <Send />}
              </Button>
            </Box>
            
            {messages.length > 0 && (
              <Box sx={{ mt: 1, textAlign: 'right' }}>
                <Button
                  variant="outlined"
                  size="small"
                  onClick={clearChat}
                  disabled={loading}
                >
                  Clear Chat
                </Button>
              </Box>
            )}
          </Box>
        </CardContent>
      </Card>
    </Container>
  );
};

export default Chat;