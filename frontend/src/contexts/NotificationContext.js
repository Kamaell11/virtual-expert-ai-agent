import React, { createContext, useContext, useState, useEffect } from 'react';
import { Snackbar, Alert } from '@mui/material';
import { fineTuningAPI } from '../services/api';

const NotificationContext = createContext();

export const useNotifications = () => {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotifications must be used within a NotificationProvider');
  }
  return context;
};

export const NotificationProvider = ({ children }) => {
  const [notifications, setNotifications] = useState([]);
  const [trainingModels, setTrainingModels] = useState(new Set());

  const showNotification = (message, severity = 'info', duration = 6000) => {
    const notification = {
      id: Date.now(),
      message,
      severity,
      duration,
      open: true,
    };
    setNotifications(prev => [...prev, notification]);
  };

  const closeNotification = (id) => {
    setNotifications(prev =>
      prev.map(notification =>
        notification.id === id ? { ...notification, open: false } : notification
      )
    );
  };

  const removeNotification = (id) => {
    setNotifications(prev => prev.filter(notification => notification.id !== id));
  };

  // Monitor training progress
  useEffect(() => {
    let intervalId;

    if (trainingModels.size > 0) {
      intervalId = setInterval(async () => {
        try {
          const models = await fineTuningAPI.getFineTunedModels();
          const completedModels = [];
          
          models.forEach(model => {
            if (trainingModels.has(model.id)) {
              if (model.training_status === 'completed') {
                completedModels.push(model);
                setTrainingModels(prev => {
                  const newSet = new Set(prev);
                  newSet.delete(model.id);
                  return newSet;
                });
              } else if (model.training_status === 'failed') {
                showNotification(
                  `Training failed for model "${model.name}". Please check the logs.`,
                  'error'
                );
                setTrainingModels(prev => {
                  const newSet = new Set(prev);
                  newSet.delete(model.id);
                  return newSet;
                });
              }
            }
          });

          // Show completion notifications
          completedModels.forEach(model => {
            showNotification(
              `🎉 Model "${model.name}" training completed successfully! It's now ready to use.`,
              'success',
              8000
            );
          });

        } catch (error) {
          console.error('Error checking training status:', error);
        }
      }, 5000); // Check every 5 seconds
    }

    return () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [trainingModels]);

  const startMonitoringTraining = (modelId) => {
    setTrainingModels(prev => new Set([...prev, modelId]));
    showNotification(
      'Training started! You will be notified when it completes.',
      'info',
      4000
    );
  };

  const value = {
    showNotification,
    startMonitoringTraining,
  };

  return (
    <NotificationContext.Provider value={value}>
      {children}
      {notifications.map((notification) => (
        <Snackbar
          key={notification.id}
          open={notification.open}
          autoHideDuration={notification.duration}
          onClose={() => closeNotification(notification.id)}
          onExited={() => removeNotification(notification.id)}
          anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
          sx={{ mt: 8 }}
        >
          <Alert
            onClose={() => closeNotification(notification.id)}
            severity={notification.severity}
            variant="filled"
            sx={{ width: '100%' }}
          >
            {notification.message}
          </Alert>
        </Snackbar>
      ))}
    </NotificationContext.Provider>
  );
};