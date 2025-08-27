import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Container,
  Grid,
  Button,
  Chip,
  LinearProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  MenuItem,
  FormControl,
  InputLabel,
  Select,
  Tab,
  Tabs,
  Alert,
  IconButton,
  Tooltip,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Paper,
  Divider,
  CircularProgress,
} from '@mui/material';
import {
  Add,
  CloudUpload,
  PlayArrow,
  Stop,
  Delete,
  Visibility,
  Timeline,
  SmartToy,
  DataUsage,
  School,
} from '@mui/icons-material';
import { fineTuningAPI } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import { useNotifications } from '../contexts/NotificationContext';

const Models = () => {
  const { user } = useAuth();
  const { showNotification, startMonitoringTraining } = useNotifications();
  const [tabValue, setTabValue] = useState(0);
  const [models, setModels] = useState([]);
  const [baseModels, setBaseModels] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  // Dialogs state
  const [createModelOpen, setCreateModelOpen] = useState(false);
  const [uploadDatasetOpen, setUploadDatasetOpen] = useState(false);
  const [trainingLogsOpen, setTrainingLogsOpen] = useState(false);
  
  // Selected model for operations
  const [selectedModel, setSelectedModel] = useState(null);
  
  // Form state
  const [newModel, setNewModel] = useState({
    model_name: '',
    base_model: '',
    specialization: '',
    description: '',
  });
  
  const [uploadFile, setUploadFile] = useState(null);
  const [uploadDescription, setUploadDescription] = useState('');
  const [trainingLogs, setTrainingLogs] = useState([]);

  useEffect(() => {
    loadModels();
    loadBaseModels();
    
    // Auto-refresh every 10 seconds for training progress
    const interval = setInterval(loadModels, 10000);
    return () => clearInterval(interval);
  }, []);

  const loadModels = async () => {
    try {
      const response = await fineTuningAPI.getFineTunedModels();
      setModels(response);
      setError('');
      
      // Debug: Log training progress
      const trainingModels = response.filter(m => m.training_status === 'training');
      if (trainingModels.length > 0) {
        console.log('Training models progress:', trainingModels.map(m => `${m.name}: ${m.training_progress}%`));
      }
    } catch (err) {
      setError('Failed to load models: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const loadBaseModels = async () => {
    try {
      const response = await fineTuningAPI.getBaseModels();
      setBaseModels(response.models);
    } catch (err) {
      console.error('Failed to load base models:', err);
    }
  };

  const handleCreateModel = async () => {
    try {
      await fineTuningAPI.createFineTunedModel(newModel);
      setCreateModelOpen(false);
      setNewModel({
        model_name: '',
        base_model: '',
        specialization: '',
        description: '',
      });
      showNotification(`Model "${newModel.model_name}" created successfully!`, 'success');
      loadModels();
    } catch (err) {
      setError('Failed to create model: ' + err.message);
      showNotification('Failed to create model: ' + err.message, 'error');
    }
  };

  const handleUploadDataset = async () => {
    if (!uploadFile || !selectedModel) return;
    
    try {
      // Auto-detect file type from extension
      const fileExtension = uploadFile.name.split('.').pop().toLowerCase();
      const datasetType = fileExtension === 'json' ? 'jsonl' : fileExtension;
      
      await fineTuningAPI.uploadDataset(
        selectedModel.id,
        uploadFile,
        datasetType,
        uploadDescription
      );
      setUploadDatasetOpen(false);
      setUploadFile(null);
      setUploadDescription('');
      showNotification(`Dataset uploaded successfully to "${selectedModel.name}"!`, 'success');
      loadModels();
    } catch (err) {
      setError('Failed to upload dataset: ' + err.message);
      showNotification('Failed to upload dataset: ' + err.message, 'error');
    }
  };

  const handleStartTraining = async (modelId) => {
    try {
      await fineTuningAPI.startTraining(modelId, {
        max_steps: 50,
        learning_rate: 0.0001,
      });
      startMonitoringTraining(modelId);
      loadModels();
    } catch (err) {
      setError('Failed to start training: ' + err.message);
      showNotification('Failed to start training: ' + err.message, 'error');
    }
  };

  const handleStopTraining = async (modelId) => {
    try {
      await fineTuningAPI.stopTraining(modelId);
      loadModels();
    } catch (err) {
      setError('Failed to stop training: ' + err.message);
    }
  };

  const handleDeleteModel = async (modelId) => {
    if (window.confirm('Are you sure you want to delete this model?')) {
      try {
        await fineTuningAPI.deleteFineTunedModel(modelId);
        loadModels();
      } catch (err) {
        setError('Failed to delete model: ' + err.message);
      }
    }
  };

  const openTrainingLogs = async (model) => {
    setSelectedModel(model);
    try {
      const logs = await fineTuningAPI.getTrainingLogs(model.id);
      setTrainingLogs(logs);
      setTrainingLogsOpen(true);
    } catch (err) {
      setError('Failed to load training logs: ' + err.message);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'training':
        return 'primary';
      case 'failed':
        return 'error';
      case 'stopped':
        return 'warning';
      default:
        return 'default';
    }
  };

  const getSpecializationIcon = (specialization) => {
    switch (specialization?.toLowerCase()) {
      case 'medical':
        return '🏥';
      case 'legal':
        return '⚖️';
      case 'mechanic':
        return '🔧';
      default:
        return '🤖';
    }
  };

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
          Fine-Tuned Models
        </Typography>
        <Typography variant="body1" color="textSecondary">
          Manage your specialized AI models and training datasets.
        </Typography>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={tabValue} onChange={(e, v) => setTabValue(v)}>
          <Tab label="My Models" />
          <Tab label="Training Status" />
        </Tabs>
      </Box>

      {tabValue === 0 && (
        <Box>
          <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between' }}>
            <Button
              variant="contained"
              startIcon={<Add />}
              onClick={() => setCreateModelOpen(true)}
            >
              Create New Model
            </Button>
          </Box>

          <Grid container spacing={3}>
            {models.map((model) => (
              <Grid item xs={12} md={6} lg={4} key={model.id}>
                <Card>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <Typography variant="h2" sx={{ mr: 1, fontSize: '1.5rem' }}>
                        {getSpecializationIcon(model.specialization)}
                      </Typography>
                      <Box>
                        <Typography variant="h6" noWrap>
                          {model.name}
                        </Typography>
                        <Typography variant="caption" color="textSecondary">
                          {model.specialization} • {model.base_model}
                        </Typography>
                      </Box>
                    </Box>

                    <Box sx={{ mb: 2 }}>
                      <Chip
                        label={model.training_status}
                        color={getStatusColor(model.training_status)}
                        size="small"
                        sx={{ mr: 1 }}
                      />
                      {model.training_status === 'training' && (
                        <Box sx={{ mt: 1 }}>
                          <LinearProgress 
                            variant="determinate" 
                            value={model.training_progress || 0}
                            sx={{ mb: 1 }}
                          />
                          <Typography variant="caption">
                            {model.training_progress || 0}% Complete
                          </Typography>
                        </Box>
                      )}
                    </Box>

                    <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                      {model.description || 'No description provided'}
                    </Typography>

                    <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                      {model.training_status === 'pending' && (
                        <>
                          <Tooltip title="Upload Dataset">
                            <IconButton
                              size="small"
                              onClick={() => {
                                setSelectedModel(model);
                                setUploadDatasetOpen(true);
                              }}
                            >
                              <CloudUpload />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Start Training">
                            <IconButton
                              size="small"
                              onClick={() => handleStartTraining(model.id)}
                            >
                              <PlayArrow />
                            </IconButton>
                          </Tooltip>
                        </>
                      )}
                      
                      {model.training_status === 'training' && (
                        <Tooltip title="Stop Training">
                          <IconButton
                            size="small"
                            onClick={() => handleStopTraining(model.id)}
                          >
                            <Stop />
                          </IconButton>
                        </Tooltip>
                      )}
                      
                      <Tooltip title="View Logs">
                        <IconButton
                          size="small"
                          onClick={() => openTrainingLogs(model)}
                        >
                          <Timeline />
                        </IconButton>
                      </Tooltip>
                      
                      <Tooltip title="Delete Model">
                        <IconButton
                          size="small"
                          onClick={() => handleDeleteModel(model.id)}
                          color="error"
                        >
                          <Delete />
                        </IconButton>
                      </Tooltip>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            ))}
            
            {models.length === 0 && (
              <Grid item xs={12}>
                <Paper sx={{ p: 4, textAlign: 'center' }}>
                  <School sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                  <Typography variant="h6" color="textSecondary" gutterBottom>
                    No Models Yet
                  </Typography>
                  <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                    Create your first fine-tuned model to get started.
                  </Typography>
                  <Button
                    variant="contained"
                    startIcon={<Add />}
                    onClick={() => setCreateModelOpen(true)}
                  >
                    Create New Model
                  </Button>
                </Paper>
              </Grid>
            )}
          </Grid>
        </Box>
      )}

      {tabValue === 1 && (
        <Box>
          <Typography variant="h6" gutterBottom>
            Training Progress
          </Typography>
          {models.filter(m => m.training_status === 'training').length === 0 ? (
            <Paper sx={{ p: 4, textAlign: 'center' }}>
              <DataUsage sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
              <Typography variant="body1" color="textSecondary">
                No active training sessions.
              </Typography>
            </Paper>
          ) : (
            models
              .filter(m => m.training_status === 'training')
              .map((model) => (
                <Card key={model.id} sx={{ mb: 2 }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <Typography variant="h2" sx={{ mr: 2, fontSize: '1.5rem' }}>
                        {getSpecializationIcon(model.specialization)}
                      </Typography>
                      <Box sx={{ flexGrow: 1 }}>
                        <Typography variant="h6">
                          {model.name}
                        </Typography>
                        <Typography variant="body2" color="textSecondary">
                          {model.specialization} Model Training
                        </Typography>
                      </Box>
                      <Button
                        size="small"
                        onClick={() => openTrainingLogs(model)}
                        startIcon={<Visibility />}
                      >
                        View Logs
                      </Button>
                    </Box>
                    
                    <Box sx={{ mb: 1 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                        <Typography variant="body2">
                          Training Progress
                        </Typography>
                        <Typography variant="body2">
                          {model.training_progress || 0}%
                        </Typography>
                      </Box>
                      <LinearProgress 
                        variant="determinate" 
                        value={model.training_progress || 0}
                      />
                    </Box>
                  </CardContent>
                </Card>
              ))
          )}
        </Box>
      )}

      {/* Create Model Dialog */}
      <Dialog open={createModelOpen} onClose={() => setCreateModelOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create New Fine-Tuned Model</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Model Name"
            value={newModel.model_name}
            onChange={(e) => setNewModel({...newModel, model_name: e.target.value})}
            margin="normal"
          />
          
          <FormControl fullWidth margin="normal">
            <InputLabel>Base Model</InputLabel>
            <Select
              value={newModel.base_model}
              onChange={(e) => setNewModel({...newModel, base_model: e.target.value, specialization: ''})}
            >
              {Object.entries(baseModels).map(([key, model]) => (
                <MenuItem key={key} value={key}>
                  {model.name} - {model.description}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          
          <FormControl fullWidth margin="normal">
            <InputLabel>Specialization</InputLabel>
            <Select
              value={newModel.specialization}
              onChange={(e) => setNewModel({...newModel, specialization: e.target.value})}
            >
              {newModel.base_model && baseModels[newModel.base_model]?.specializations?.map(spec => {
                const icons = {
                  'medical': '🏥',
                  'legal': '⚖️',
                  'mechanic': '🔧',
                  'general_chat': '💬',
                  'customer_service': '🎧'
                };
                const labels = {
                  'medical': 'Medical',
                  'legal': 'Legal',
                  'mechanic': 'Mechanic',
                  'general_chat': 'General Chat',
                  'customer_service': 'Customer Service'
                };
                return (
                  <MenuItem key={spec} value={spec}>
                    {icons[spec] || '🤖'} {labels[spec] || spec}
                  </MenuItem>
                );
              })}
              {(!newModel.base_model || !baseModels[newModel.base_model]) && (
                <MenuItem disabled>Select a base model first</MenuItem>
              )}
            </Select>
          </FormControl>
          
          <TextField
            fullWidth
            label="Description"
            multiline
            rows={3}
            value={newModel.description}
            onChange={(e) => setNewModel({...newModel, description: e.target.value})}
            margin="normal"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateModelOpen(false)}>Cancel</Button>
          <Button 
            onClick={handleCreateModel}
            variant="contained"
            disabled={!newModel.model_name || !newModel.base_model || !newModel.specialization}
          >
            Create
          </Button>
        </DialogActions>
      </Dialog>

      {/* Upload Dataset Dialog */}
      <Dialog open={uploadDatasetOpen} onClose={() => setUploadDatasetOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Upload Training Dataset</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
            Upload training data for: <strong>{selectedModel?.name}</strong>
            <br />
            Supported formats: JSONL, CSV, PDF, TXT
          </Typography>
          
          <input
            type="file"
            accept=".jsonl,.json,.csv,.pdf,.txt"
            onChange={(e) => setUploadFile(e.target.files[0])}
            style={{ margin: '16px 0' }}
          />
          
          <TextField
            fullWidth
            label="Dataset Description"
            multiline
            rows={2}
            value={uploadDescription}
            onChange={(e) => setUploadDescription(e.target.value)}
            margin="normal"
            helperText="Describe what type of data this dataset contains"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setUploadDatasetOpen(false)}>Cancel</Button>
          <Button 
            onClick={handleUploadDataset}
            variant="contained"
            disabled={!uploadFile}
            startIcon={<CloudUpload />}
          >
            Upload
          </Button>
        </DialogActions>
      </Dialog>

      {/* Training Logs Dialog */}
      <Dialog open={trainingLogsOpen} onClose={() => setTrainingLogsOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          Training Logs - {selectedModel?.name}
        </DialogTitle>
        <DialogContent>
          <List>
            {trainingLogs.map((log, index) => (
              <ListItem key={log.id || index}>
                <ListItemText
                  primary={log.message}
                  secondary={
                    <Box>
                      <Typography variant="caption" display="block">
                        {new Date(log.created_at).toLocaleString()}
                      </Typography>
                      {(log.loss || log.accuracy) && (
                        <Typography variant="caption">
                          {log.loss && `Loss: ${log.loss}`}
                          {log.loss && log.accuracy && ' • '}
                          {log.accuracy && `Accuracy: ${log.accuracy}`}
                        </Typography>
                      )}
                    </Box>
                  }
                />
                <Chip 
                  label={log.log_level} 
                  size="small" 
                  color={log.log_level === 'ERROR' ? 'error' : log.log_level === 'WARNING' ? 'warning' : 'primary'}
                />
              </ListItem>
            ))}
          </List>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setTrainingLogsOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default Models;