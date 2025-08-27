import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { Box } from '@mui/material';

import { useAuth } from './contexts/AuthContext';
import Navbar from './components/Navbar';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Chat from './pages/Chat';
import History from './pages/History';
import Models from './pages/Models';
import Profile from './pages/Profile';
import TestAuth from './pages/TestAuth';

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
    background: {
      default: '#f5f5f5',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    h4: {
      fontWeight: 600,
    },
    h5: {
      fontWeight: 600,
    },
  },
});

function App() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Box
          display="flex"
          justifyContent="center"
          alignItems="center"
          minHeight="100vh"
        >
          Loading...
        </Box>
      </ThemeProvider>
    );
  }

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
          {user && <Navbar />}
          <Box component="main" sx={{ flexGrow: 1 }}>
            <Routes>
              {!user ? (
                <>
                  <Route path="/login" element={<Login />} />
                  <Route path="/register" element={<Register />} />
                  <Route path="/test" element={<TestAuth />} />
                  <Route path="*" element={<Navigate to="/login" replace />} />
                </>
              ) : (
                <>
                  <Route path="/" element={<Dashboard />} />
                  <Route path="/chat" element={<Chat />} />
                  <Route path="/history" element={<History />} />
                  <Route path="/models" element={<Models />} />
                  <Route path="/profile" element={<Profile />} />
                  <Route path="/login" element={<Navigate to="/" replace />} />
                  <Route path="/register" element={<Navigate to="/" replace />} />
                </>
              )}
            </Routes>
          </Box>
        </Box>
      </Router>
    </ThemeProvider>
  );
}

export default App;