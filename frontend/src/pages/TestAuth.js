import React, { useState } from 'react';
import { Box, Button, Typography, Alert } from '@mui/material';
import { useAuth } from '../contexts/AuthContext';

const TestAuth = () => {
  const { login, register: registerUser } = useAuth();
  const [result, setResult] = useState('');

  const testLogin = async () => {
    console.log('Testing login...');
    try {
      const result = await login('kamil', '123456');
      console.log('Login result:', result);
      setResult(`Login: ${JSON.stringify(result)}`);
    } catch (error) {
      console.error('Login error:', error);
      setResult(`Login Error: ${error.message}`);
    }
  };

  const testRegister = async () => {
    console.log('Testing registration...');
    try {
      const result = await registerUser('testuser123', 'password123', 'test@test.com');
      console.log('Register result:', result);
      setResult(`Register: ${JSON.stringify(result)}`);
    } catch (error) {
      console.error('Register error:', error);
      setResult(`Register Error: ${error.message}`);
    }
  };

  return (
    <Box p={4}>
      <Typography variant="h4" gutterBottom>
        Auth Test Page
      </Typography>
      
      <Box mb={2}>
        <Button variant="contained" onClick={testLogin} sx={{ mr: 2 }}>
          Test Login (kamil/123456)
        </Button>
        <Button variant="outlined" onClick={testRegister}>
          Test Register (testuser123)
        </Button>
      </Box>

      {result && (
        <Alert severity="info" sx={{ mt: 2 }}>
          {result}
        </Alert>
      )}
    </Box>
  );
};

export default TestAuth;